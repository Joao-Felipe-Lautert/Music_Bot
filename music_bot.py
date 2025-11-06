import discord
from discord.ext import commands
import yt_dlp
import asyncio

# 1. CONFIGURAÇÃO INICIAL
# -----------------------------------------------------------------------------
# Defina as permissões (Intents) que o bot precisa.
# message_content é necessário para ler os comandos.
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# O prefixo do seu bot (ex: !, ?, etc.)
bot = commands.Bot(command_prefix="!", intents=intents)

# Configurações do FFMPEG (necessário para o áudio)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Configurações do yt-dlp
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues
}

# Dicionários para armazenar as filas e músicas atuais por servidor
queues = {}
current_song = {}

# 2. FUNÇÕES AUXILIARES DE MÚSICA
# -----------------------------------------------------------------------------

async def play_next(ctx):
    """
    Função auxiliar para tocar a próxima música na fila.
    É chamada automaticamente quando uma música termina.
    """
    guild_id = ctx.guild.id
    if guild_id in queues and queues[guild_id]:
        # Pega a próxima música da fila
        next_song = queues[guild_id].pop(0)
        url = next_song['url']
        title = next_song['title']
        
        # Cria a fonte de áudio e começa a tocar
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(
            source, 
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        )
        
        current_song[guild_id] = title
        await ctx.send(f"🎶 Tocando agora: **{title}**")
    else:
        # Fila está vazia
        current_song[guild_id] = None
        await ctx.send("Fila terminada.")
        # Opcional: Desconectar após um tempo de inatividade

async def search_youtube(search_query):
    """
    Busca no YouTube (ou link direto) e retorna o URL do áudio e o título.
    """
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        try:
            # Tenta buscar como um termo de pesquisa
            info = ydl.extract_info(f"ytsearch:{search_query}", download=False)
            if 'entries' in info and info['entries']:
                # Pega o primeiro resultado da busca
                video = info['entries'][0]
            else:
                # Se não for busca, pode ser um link direto
                video = ydl.extract_info(search_query, download=False)

        except Exception as e:
            print(f"Erro ao buscar música: {e}")
            return None, None

        # Retorna o URL do stream e o título
        return video['url'], video['title']

# 3. EVENTOS DO BOT
# -----------------------------------------------------------------------------

@bot.event
async def on_ready():
    """Chamado quando o bot está online e pronto."""
    print(f'Bot {bot.user.name} está online!')
    await bot.change_presence(activity=discord.Game(name="Música | !play"))

# 4. COMANDOS DE MÚSICA
# -----------------------------------------------------------------------------

@bot.command(name='play', aliases=['p', 'tocar'], help="Toca uma música do YouTube (busca ou link)")
async def play(ctx, *, search: str):
    """
    Comando !play <nome da música ou link>
    """
    # 1. Verificar se o autor do comando está em um canal de voz
    if not ctx.author.voice:
        await ctx.send("Você precisa estar em um canal de voz para usar este comando!")
        return

    voice_channel = ctx.author.voice.channel
    
    # 2. Conectar ao canal de voz (se já não estiver)
    if not ctx.voice_client:
        try:
            await voice_channel.connect()
        except discord.errors.ClientException:
            await ctx.send("Eu já estou em um canal de voz!")
            return
        except Exception as e:
            await ctx.send(f"Erro ao conectar ao canal de voz: {e}")
            return
    
    await ctx.send(f"🔎 Procurando por: **{search}**...")
    
    # 3. Buscar a música
    url, title = await search_youtube(search)
    
    if not url:
        await ctx.send("Desculpe, não consegui encontrar essa música.")
        return

    song = {'url': url, 'title': title}
    guild_id = ctx.guild.id

    # 4. Adicionar à fila
    if guild_id not in queues:
        queues[guild_id] = []
        
    # 5. Tocar ou Adicionar à fila
    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        # Se nada estiver tocando, toca imediatamente
        queues[guild_id].append(song) # Adiciona para o caso de !skip
        await play_next(ctx) # A função play_next vai pegar a música da fila
    else:
        # Se já estiver tocando, adiciona na fila
        queues[guild_id].append(song)
        await ctx.send(f"✅ Adicionado à fila: **{title}**")

@bot.command(name='pause', aliases=['pausar'], help="Pausa a música atual")
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Música pausada.")
    else:
        await ctx.send("Não há música tocando para pausar.")

@bot.command(name='resume', aliases=['continuar'], help="Continua a música pausada")
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Música continuada.")
    else:
        await ctx.send("A música não está pausada.")

@bot.command(name='skip', aliases=['pular'], help="Pula para a próxima música na fila")
async def skip(ctx):
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        ctx.voice_client.stop() # Isso vai acionar o 'after' na função play()
        await ctx.send("⏭️ Música pulada.")
        # play_next será chamado automaticamente
    else:
        await ctx.send("Não há música tocando para pular.")

@bot.command(name='stop', aliases=['parar'], help="Para a música e limpa a fila")
async def stop(ctx):
    guild_id = ctx.guild.id
    
    # Limpa a fila
    if guild_id in queues:
        queues[guild_id] = []
        
    current_song[guild_id] = None
    
    if ctx.voice_client:
        # Para de tocar
        ctx.voice_client.stop()
        # Sai do canal de voz
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Reprodução parada, fila limpa e bot desconectado.")
    else:
        await ctx.send("Eu não estou em um canal de voz.")

@bot.command(name='queue', aliases=['q', 'fila'], help="Mostra a fila de músicas")
async def queue(ctx):
    guild_id = ctx.guild.id
    
    if guild_id not in queues or not queues[guild_id]:
        await ctx.send("A fila está vazia.")
        return

    # Cria uma lista de strings para a fila
    queue_list = []
    for i, song in enumerate(queues[guild_id]):
        queue_list.append(f"{i + 1}. {song['title']}")

    # Formata a lista para exibição
    # Pega o que está tocando agora
    now_playing = current_song.get(guild_id)
    if not now_playing:
        now_playing = "Nada"

    # Cria uma "embed" bonita do Discord
    embed = discord.Embed(
        title="Fila de Músicas",
        color=discord.Color.blue()
    )
    embed.add_field(name="Tocando Agora", value=f"**{now_playing}**", inline=False)
    
    if queue_list:
        # Limita a 10 músicas para não poluir o chat
        embed.add_field(name="Próximas", value="\n".join(queue_list[:10]), inline=False)
        if len(queue_list) > 10:
            embed.set_footer(text=f"e mais {len(queue_list) - 10}...")
            
    await ctx.send(embed=embed)

@bot.command(name='nowplaying', aliases=['np', 'tocando'], help="Mostra a música que está tocando")
async def nowplaying(ctx):
    guild_id = ctx.guild.id
    title = current_song.get(guild_id)
    
    if title:
        await ctx.send(f"🎶 Tocando agora: **{title}**")
    else:
        await ctx.send("Não há nada tocando no momento.")

# 5. INICIAR O BOT
# -----------------------------------------------------------------------------
# Substitua "SEU_TOKEN_AQUI" pelo token do seu bot
bot.run("MTQzNTc5MTAyNzEwNDM4NzE3Mw.GWwrK4.0i3E3HzmoPshaZVjGxaXinaN2fQ7BamWFgrevw")