
# Devolutiva formativa — Atividade 02 da SA

**Estudante:** Kauan Weiss  
**Turma:** São Bento do Sul — Manhã  
**Unidade Curricular:** Programação de Aplicativos  
**Projeto:** Tema divergente — Transporte (Python) / Fábrica de chocolate (HTML)  
**Repositório:** https://github.com/kauanweiss87-pixel/SA-Kauan  
**Arquivos observados:** `codigo/app.py`, `interface/index.html` e `interface/style.css`  
**Data da verificação:** 23/11/2026  
**Escopo:** evidências técnicas dos critérios CT6 e CT7, sem atribuição de nota numérica.

## Situação atual do projeto

Há duas propostas diferentes no repositório. O arquivo `codigo/app.py` implementa um servidor HTTP com SQLite para um aplicativo de transporte. Já a interface HTML/CSS apresenta uma fábrica de chocolate com informações institucionais, lista de produtos e contato, mas sem formulários ou ações de negócio. Essa diferença impede demonstrar uma única solução consistente da SA no estado atual.

## Pontos positivos identificados

- O arquivo Python contém funções para estimar tarifas, selecionar motoristas, solicitar corridas, alterar situações e consultar dados no SQLite.
- Há uma tentativa de organizar API, tratamento de erros e armazenamento usando a biblioteca padrão do Python.
- O HTML da fábrica possui títulos, listas e organização legível.
- O CSS utiliza estilos separados para títulos, textos, listas e rodapé.

## O que precisa ser corrigido ou concluído

### 1. Definir um único projeto para a entrega

O Python trata de *transporte* e a interface mostra *fábrica de chocolate*. **Como melhorar:** decidir qual é o projeto da SA e fazer código e interface representarem o mesmo problema. Não é necessário refazer tudo: pode aproveitar a solução que pretende continuar.

### 2. Tornar a interface funcional

A página da fábrica é informativa e não permite cadastrar produção, consultar estoque ou executar outra operação do sistema. **Como melhorar:** se escolher chocolate, adicionar ao menos um formulário com validação e resultado; se escolher transporte, preparar uma página para origem, destino, categoria e estimativa.

### 3. Corrigir a instrução de execução do Python

O comentário de `codigo/app.py` informa `python server.py`, mas o arquivo publicado se chama `app.py`. **Como melhorar:** corrigir o comando no cabeçalho e no README e verificar os caminhos de arquivos servidos.

### 4. Conferir o diretório de arquivos estáticos

O servidor Python aponta para uma pasta `static` ao lado do código, enquanto a página publicada está na pasta `interface`. **Como melhorar:** adequar os caminhos à estrutura real ou organizar os arquivos na pasta esperada.

## Oportunidades de melhoria

- Adicionar funções curtas e reutilizáveis relacionadas ao tema definitivo.
- Registrar no README quais ações o usuário consegue executar e quais ainda são planejadas.
- Testar erros de entrada e manter a interface alinhada aos nomes utilizados no Python.

## Testes recomendados

1. Confirmar qual é o tema final com o professor.
2. Executar o Python pelo nome correto do arquivo.
3. Verificar se o HTML e o CSS são encontrados pelo servidor, caso haja integração.
4. Fazer uma operação completa do tema escolhido usando a interface.
5. Testar entradas vazias, quantidades negativas ou locais inválidos, conforme o projeto.

## Prioridades para a próxima versão

1. **Escolher e manter um único tema em todos os arquivos.**
2. **Construir pelo menos uma operação funcional na interface.**
3. **Corrigir instruções e caminhos de execução.**
4. **Documentar e demonstrar o fluxo completo da funcionalidade.**

## Mensagem final

Kauan, há trabalho técnico tanto no Python quanto na apresentação HTML. O principal passo agora é reunir esses esforços em um único sistema, de modo que a interface represente o mesmo problema resolvido pelo código.

---
