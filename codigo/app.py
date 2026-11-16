"""Servidor do aplicativo de transporte.
Usa apenas a biblioteca padrão do Python (http.server + sqlite3): não precisa instalar nada.
Execute:  python server.py   e abra  http://localhost:8000
"""
import json, math, os, sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "transporte.db")
STATIC = os.path.join(BASE, "static")
PASSAGEIRO_ID = 1  # sem login nesta versão: usamos o passageiro de exemplo

TARIFAS = {  # RN01: base + km * valor_km, respeitando o mínimo
    "economico": {"base": 5.0, "km": 2.2, "min": 8.0},
    "conforto": {"base": 7.0, "km": 3.1, "min": 12.0},
}


class Erro(Exception):
    def __init__(self, msg, codigo=400):
        super().__init__(msg)
        self.codigo = codigo


def conectar():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def iniciar_banco():
    if os.path.exists(DB_PATH):
        return
    db = conectar()
    with open(os.path.join(BASE, "schema.sql"), encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()
    db.close()


# ---------- regras de negócio ----------
def distancia_km(db, origem_id, destino_id):
    a = db.execute("SELECT latitude, longitude FROM lugar WHERE id=?", (origem_id,)).fetchone()
    b = db.execute("SELECT latitude, longitude FROM lugar WHERE id=?", (destino_id,)).fetchone()
    if not a or not b:
        raise Erro("Local não encontrado.", 404)
    r = math.radians
    h = (math.sin(r(b[0] - a[0]) / 2) ** 2
         + math.cos(r(a[0])) * math.cos(r(b[0])) * math.sin(r(b[1] - a[1]) / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(h)) * 1.3  # 1,3 = fator de sinuosidade das ruas


def calcular_tarifa(dist, categoria):
    t = TARIFAS.get(categoria)
    if not t:
        raise Erro("Categoria inválida.")
    return round(max(t["min"], t["base"] + dist * t["km"]), 2)


def motorista_mais_proximo(db, origem_id, categoria):
    """RF04/RN02: motorista online, da categoria pedida e sem corrida ativa, mais próximo da origem."""
    linhas = db.execute("""
        SELECT m.usuario_id, l.latitude, l.longitude
        FROM motorista m
        JOIN veiculo v ON v.motorista_id = m.usuario_id
        JOIN lugar l ON l.id = m.lugar_id
        WHERE m.online = 1 AND v.categoria = ?
          AND m.usuario_id NOT IN (SELECT motorista_id FROM corrida
               WHERE status IN ('aceita','em_andamento') AND motorista_id IS NOT NULL)
    """, (categoria,)).fetchall()
    o = db.execute("SELECT latitude, longitude FROM lugar WHERE id=?", (origem_id,)).fetchone()
    melhor, menor = None, float("inf")
    for m in linhas:
        d = math.hypot(m["latitude"] - o["latitude"], m["longitude"] - o["longitude"])
        if d < menor:
            melhor, menor = m["usuario_id"], d
    return melhor


def estado(db):
    lugares = [dict(r) for r in db.execute("SELECT id, nome FROM lugar ORDER BY id")]
    motoristas = [dict(r) for r in db.execute("""
        SELECT u.id, u.nome, m.online, l.nome AS local, v.categoria, v.modelo,
          (SELECT ROUND(AVG(a.nota),1) FROM avaliacao a JOIN corrida c ON c.id=a.corrida_id
            WHERE c.motorista_id = u.id) AS nota
        FROM motorista m JOIN usuario u ON u.id=m.usuario_id
        JOIN veiculo v ON v.motorista_id=m.usuario_id
        LEFT JOIN lugar l ON l.id=m.lugar_id ORDER BY u.id""")]
    corridas = [dict(r) for r in db.execute("""
        SELECT c.id, lo.nome AS origem, ld.nome AS destino, c.categoria, c.distancia_km,
               c.tarifa, c.status, u.nome AS motorista, p.metodo AS pagamento,
               (SELECT nota FROM avaliacao WHERE corrida_id=c.id AND autor_id=c.passageiro_id) AS nota
        FROM corrida c
        JOIN lugar lo ON lo.id=c.origem_id JOIN lugar ld ON ld.id=c.destino_id
        LEFT JOIN usuario u ON u.id=c.motorista_id
        LEFT JOIN pagamento p ON p.corrida_id=c.id
        ORDER BY c.id DESC""")]
    return {"lugares": lugares, "motoristas": motoristas, "corridas": corridas}


def estimar(db, q):
    o, d, cat = int(q["origem"][0]), int(q["destino"][0]), q["categoria"][0]
    if o == d:
        raise Erro("Origem e destino devem ser diferentes.")
    dist = distancia_km(db, o, d)
    return {"distancia_km": round(dist, 1), "tarifa": calcular_tarifa(dist, cat)}


def solicitar(db, dados):
    o, d = int(dados["origem"]), int(dados["destino"])
    cat, metodo = dados["categoria"], dados["pagamento"]
    if o == d:
        raise Erro("Origem e destino devem ser diferentes.")
    if metodo not in ("cartao", "pix", "dinheiro"):
        raise Erro("Forma de pagamento inválida.")
    dist = distancia_km(db, o, d)
    tarifa = calcular_tarifa(dist, cat)
    mot = motorista_mais_proximo(db, o, cat)
    cur = db.execute(
        "INSERT INTO corrida (passageiro_id, motorista_id, origem_id, destino_id, categoria,"
        " distancia_km, tarifa, status) VALUES (?,?,?,?,?,?,?,?)",
        (PASSAGEIRO_ID, mot, o, d, cat, dist, tarifa, "aceita" if mot else "solicitada"))
    db.execute("INSERT INTO pagamento (corrida_id, metodo, valor) VALUES (?,?,?)",
               (cur.lastrowid, metodo, tarifa))
    return {"id": cur.lastrowid, "pareada": mot is not None}


def mudar_status(db, corrida_id, acao):
    c = db.execute("SELECT * FROM corrida WHERE id=?", (corrida_id,)).fetchone()
    if not c:
        raise Erro("Corrida não encontrada.", 404)
    st = c["status"]
    if acao == "parear" and st == "solicitada":
        mot = motorista_mais_proximo(db, c["origem_id"], c["categoria"])
        if not mot:
            raise Erro("Nenhum motorista disponível agora.")
        db.execute("UPDATE corrida SET motorista_id=?, status='aceita' WHERE id=?", (mot, corrida_id))
    elif acao == "iniciar" and st == "aceita":
        db.execute("UPDATE corrida SET status='em_andamento' WHERE id=?", (corrida_id,))
    elif acao == "concluir" and st == "em_andamento":
        db.execute("UPDATE corrida SET status='concluida', concluida_em=CURRENT_TIMESTAMP WHERE id=?", (corrida_id,))
        db.execute("UPDATE pagamento SET pago_em=CURRENT_TIMESTAMP WHERE corrida_id=?", (corrida_id,))
        db.execute("UPDATE motorista SET lugar_id=? WHERE usuario_id=?", (c["destino_id"], c["motorista_id"]))
    elif acao == "cancelar" and st in ("solicitada", "aceita"):  # RN03
        db.execute("UPDATE corrida SET status='cancelada' WHERE id=?", (corrida_id,))
    else:
        raise Erro(f"Não é possível '{acao}' uma corrida {st}.")


def avaliar(db, corrida_id, nota):
    c = db.execute("SELECT status FROM corrida WHERE id=?", (corrida_id,)).fetchone()
    if not c or c["status"] != "concluida":  # RN04
        raise Erro("Só corridas concluídas podem ser avaliadas.")
    if not 1 <= int(nota) <= 5:
        raise Erro("A nota deve ser de 1 a 5.")
    try:
        db.execute("INSERT INTO avaliacao (corrida_id, autor_id, nota) VALUES (?,?,?)",
                   (corrida_id, PASSAGEIRO_ID, int(nota)))
    except sqlite3.IntegrityError:
        raise Erro("Esta corrida já foi avaliada.")


def alternar_online(db, motorista_id):
    db.execute("UPDATE motorista SET online = 1 - online WHERE usuario_id=?", (motorista_id,))


# ---------- HTTP ----------
class Handler(BaseHTTPRequestHandler):
    def responder(self, dados, codigo=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path.startswith("/api/"):
            return self.api(lambda db: estado(db) if url.path == "/api/estado"
                            else estimar(db, parse_qs(url.query)) if url.path == "/api/estimativa"
                            else (_ for _ in ()).throw(Erro("Rota não encontrada.", 404)))
        arq = "index.html" if url.path == "/" else url.path.lstrip("/")
        caminho = os.path.normpath(os.path.join(STATIC, arq))
        if not caminho.startswith(STATIC) or not os.path.isfile(caminho):
            return self.responder({"erro": "Não encontrado."}, 404)
        tipos = {".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript"}
        with open(caminho, "rb") as f:
            corpo = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipos.get(os.path.splitext(caminho)[1], "application/octet-stream"))
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        partes = urlparse(self.path).path.strip("/").split("/")
        tam = int(self.headers.get("Content-Length") or 0)
        dados = json.loads(self.rfile.read(tam) or b"{}")

        def rota(db):
            if partes == ["api", "corridas"]:
                return solicitar(db, dados)
            if len(partes) == 4 and partes[:2] == ["api", "corridas"]:
                if partes[3] == "avaliar":
                    return avaliar(db, int(partes[2]), dados.get("nota", 0)) or {"ok": True}
                return mudar_status(db, int(partes[2]), partes[3]) or {"ok": True}
            if len(partes) == 4 and partes[:2] == ["api", "motoristas"] and partes[3] == "online":
                return alternar_online(db, int(partes[2])) or {"ok": True}
            raise Erro("Rota não encontrada.", 404)
        self.api(rota, commit=True)

    def api(self, fn, commit=False):
        db = conectar()
        try:
            resultado = fn(db)
            if commit:
                db.commit()
            self.responder(resultado)
        except Erro as e:
            db.rollback()
            self.responder({"erro": str(e)}, e.codigo)
        except (KeyError, ValueError, TypeError):
            db.rollback()
            self.responder({"erro": "Dados inválidos."}, 400)
        finally:
            db.close()

    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path}")


if __name__ == "__main__":
    iniciar_banco()
    porta = int(os.environ.get("PORT", 8000))
    print(f"Servidor em http://localhost:{porta}  (Ctrl+C para parar)")
    ThreadingHTTPServer(("127.0.0.1", porta), Handler).serve_forever()
