<h1>🎶 Bot de Música para Discord</h1>
Este é um bot de música simples para o Discord, escrito em Python, que utiliza as bibliotecas discord.py e yt-dlp.

Ele permite que os usuários solicitem músicas do YouTube (através de links ou termos de busca), gerenciem uma fila de reprodução, pausem, pulem e parem a música, tudo dentro de um canal de voz do Discord.

<h2>✨ Funcionalidades</h2>
Tocar música: Adiciona uma música (via link ou busca no YouTube) à fila e começa a tocar.

Pausar e Continuar: Controles básicos de reprodução.

Pular: Pula a música atual e passa para a próxima da fila.

Fila de Músicas: Visualiza as próximas músicas na fila (!queue).

Tocando Agora: Mostra qual música está tocando no momento (!np).

Parar: Limpa completamente a fila, para a reprodução e desconecta o bot do canal.

<h2>⚠️ Requisitos</h2>
Para que este bot funcione, você precisará de:

Python 3.8 ou superior.

Uma conta no Discord e privilégios de administrador em um servidor para adicionar o bot.

Um Token de Bot do Discord.

O software FFmpeg instalado e acessível no PATH do sistema.

<h2>🛠️ Instalação e Configuração</h2>
Siga estes passos para configurar o bot no seu ambiente.

1. Instale o FFmpeg (Passo Crítico!)
Este bot não funcionará sem o FFmpeg. Ele é um software usado para processar o áudio antes de enviá-lo ao Discord.

Windows:

Baixe a última versão "essentials" em gyan.dev/ffmpeg/builds/.

Descompacte o arquivo .zip (por exemplo, em C:\ffmpeg).

Adicione a pasta bin (ex: C:\ffmpeg\bin) ao seu PATH (Variáveis de Ambiente) do sistema.

Para verificar, abra um novo terminal e digite ffmpeg -version. Se informações da versão aparecerem, a instalação foi bem-sucedida.

Linux (Debian/Ubuntu):

Bash

sudo apt update
sudo apt install ffmpeg
MacOS (usando Homebrew):

Bash

brew install ffmpeg
2. Configure o Projeto Python
Clone este repositório (ou baixe os arquivos):

Bash

git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
cd SEU-REPOSITORIO
(Opcional, mas recomendado) Crie um ambiente virtual:

Bash

python -m venv venv
source venv/bin/activate  # No Linux/Mac
.\venv\Scripts\activate   # No Windows (PowerShell)
Instale as bibliotecas Python necessárias:

Bash

pip install discord.py yt-dlp PyNaCl
3. Configure o Bot no Discord
Vá até o Portal de Desenvolvedores do Discord.

Crie uma "Nova Aplicação" e dê um nome a ela.

Vá para a aba "Bot" e clique em "Add Bot".

Habilite as Intents Privilegiadas: Na mesma aba "Bot", role para baixo e ative a MESSAGE CONTENT INTENT. Isso é necessário para que o bot leia os comandos (ex: !play).

Copie o Token: Clique em "Reset Token" para revelar e copiar seu token. Nunca compartilhe este token!

4. Adicione o Token e Inicie o Bot
Abra o arquivo music_bot.py em um editor de código.

Encontre a última linha do arquivo:

Python

bot.run("SEU_TOKEN_AQUI")
Substitua "SEU_TOKEN_AQUI" pelo token que você copiou no passo anterior (mantenha as aspas).

Salve o arquivo e inicie o bot pelo seu terminal:

Bash

python music_bot.py
5. Convide o Bot para o seu Servidor
No Portal de Desenvolvedores, vá para "OAuth2" > "URL Generator".

Marque os seguintes "Scopes":

bot

Em "Bot Permissions" (Permissões do Bot), marque:

Send Messages

Embed Links

Connect

Speak

Read Message History

Copie a URL gerada na parte inferior e cole-a no seu navegador. Escolha o servidor para o qual deseja adicionar o bot.

<h2>🎵 Como Usar (Comandos)</h2>
No seu servidor Discord, entre em um canal de voz e use os seguintes comandos:

!play <nome da música ou link do YouTube>: Toca uma música ou a adiciona na fila.

!pause: Pausa a música atual.

!resume: Continua a música pausada.

!skip: Pula a música atual e toca a próxima da fila.

!stop: Para a música, limpa a fila e desconecta o bot.

!queue (ou !q): Mostra as próximas músicas na fila.

!np (ou !tocando): Mostra qual música está tocando agora.

<strong>Aviso: Este bot baixa conteúdo de plataformas de terceiros (como o YouTube). Use-o com responsabilidade e certifique-se de estar em conformidade com os Termos de Serviço do Discord e das fontes de conteúdo.</strong>
