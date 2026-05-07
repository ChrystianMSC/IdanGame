# Jogo de Cartas 1x1 (P2P Command Line)
Este é um projeto de jogo de cartas competitivo projetado para funcionar via linha de comando, permitindo que dois jogadores se enfrentem diretamente através de uma conexão **Peer-to-Peer (P2P)**.
## 👥 Integrantes
 * **Chrystian Martins Soares Costa**
## 🕹️ Explicação do Sistema
O sistema consiste em uma aplicação de terminal onde a lógica do jogo e a comunicação de rede acontecem simultaneamente. Diferente de jogos tradicionais que dependem de um servidor central, este projeto utiliza a arquitetura **P2P**, onde cada instância do jogo atua tanto como cliente quanto como servidor.
### Funcionamento Geral:
 1. **Conexão:** Um jogador atua como o "Host" (aguardando conexão) e o outro como "Guest" (conectando-se ao IP do Host).
 2. **Mecânica de Jogo:** O jogo processa turnos alternados, onde cada jogada realizada em um terminal é enviada via *socket* para o adversário.
 3. **Interface:** Toda a interação é feita via texto (CLI), exibindo o estado do tabuleiro, a mão do jogador e o log de ações.
 4. **Sincronização:** O sistema garante que ambos os jogadores visualizem o mesmo estado de jogo, validando jogadas e atualizando os pontos de vida/cartas em tempo real.
## 🛠️ Tecnologias Utilizadas
Para a implementação deste projeto, as seguintes tecnologias e conceitos são fundamentais:
 * **Linguagem de Programação:** Python
 * **Protocolo TCP/UDP:** Utilização de **Sockets** para garantir a entrega de pacotes de dados entre as duas máquinas.
 * **Multithreading:** Necessário para permitir que a interface do usuário continue funcional enquanto o sistema "escuta" as jogadas vindas da rede.
 * **Serialização de Dados (JSON):** Para converter os objetos das cartas e estados de jogo em texto para transporte via rede e posterior reconstrução no destino.
 * ** Pytest ** - testes unitários
### Como clonar o repositório
```bash
git clone https://github.com/seu-usuario/nome-do-repositorio.git

```
