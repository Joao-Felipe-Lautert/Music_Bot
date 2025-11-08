import discord
from discord.ext import commands
import yt_dlp
import asyncio

# 1. CONFIGURAÇÃO INICIAL
# -----------------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Configurações do FFMPEG
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Configurações do yt-dlp (PARA MÚSICAS ÚNICAS E BUSCAS)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,  # <-- Importante: não carrega playlists por padrão
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
    'source_address': '0.0.0.0'
}

# Configurações do yt-dlp (PARA PLAYLISTS)
YTDL_PLAYLIST_OPTIONS = YTDL_OPTIONS.copy()
YTDL_PLAYLIST_OPTIONS['noplaylist'] = False # <-- Importante: permite carregar playlists
YTDL_PLAYLIST_OPTIONS['extract_flat'] = True # Pega os vídeos da playlist mais rápido


# Dicionários de estado
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
        current_song[guild_id] = None
        await ctx.send("Fila terminada.")

async def search_youtube(search_query):
    """
    Busca no YouTube (ou link direto) - APENAS MÚSICA ÚNICA.
    Usa as YTDL_OPTIONS padrão (noplaylist=True).
    """
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(search_query, download=False)
            
            # Se for uma busca (ex: "musica"), 'entries' conterá os resultados
            if 'entries' in info and info['entries']:
                video = info['entries'][0]
            # Se for um link direto de vídeo, 'entries' não existirá
            else:
                video = info

        except Exception as e:
            print(f"Erro ao buscar música única: {e}")
            return None, None

        return video['url'], video['title']

async def extract_playlist_songs(playlist_url):
    """
    Extrai todas as músicas de uma URL de playlist do YouTube.
    Usa as YTDL_PLAYLIST_OPTIONS (noplaylist=False).
    """
    songs = []
    playlist_title = "Playlist Desconhecida"
    
    with yt_dlp.YoutubeDL(YTDL_PLAYLIST_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(playlist_url, download=False)
            playlist_title = info.get('title', playlist_title)
            
            if 'entries' in info:
                for video in info['entries']:
                    if video:
                        # Precisamos extrair a URL de áudio individual de cada
                        # (Isso torna o carregamento da playlist mais lento, mas é mais seguro)
                        try:
                            video_info = ydl.extract_info(video['url'], download=False)
                            songs.append({'url': video_info['url'], 'title': video_info['title']})
                        except Exception as e:
                            print(f"Erro ao extrair vídeo individual da playlist: {e}")
                            
        except Exception as e:
            print(f"Erro ao carregar playlist: {e}")
            return [], playlist_title

    return songs, playlist_title


# 3. EVENTOS DO BOT
# -----------------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está online!')
    await bot.change_presence(activity=discord.Game(name="Música | !play"))

# 4. COMANDOS DE MÚSICA
# -----------------------------------------------------------------------------

@bot.command(name='play', aliases=['p', 'tocar'], help="Toca uma música ou playlist do YouTube (busca, link de vídeo ou link de playlist)")
async def play(ctx, *, search: str):
    """
    Comando !play <nome da música, link do vídeo ou link da playlist>
    """
    # 1. Verificar canal de voz
    if not ctx.author.voice:
        await ctx.send("Você precisa estar em um canal de voz para usar este comando!")
        return

    voice_channel = ctx.author.voice.channel
    
    # 2. Conectar ao canal de voz
    if not ctx.voice_client:
        try:
            await voice_channel.connect()
        except Exception as e:
            await ctx.send(f"Erro ao conectar ao canal de voz: {e}")
            return
    
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []

    # 3. VERIFICAR SE É PLAYLIST OU MÚSICA ÚNICA
    # Heurística simples: URLs de playlist do YouTube contêm 'list='
    is_playlist = "list=" in search and ("youtube.com/" in search or "youtu.be/" in search)

    if is_playlist:
        # É UMA PLAYLIST
        await ctx.send(f"🔎 Carregando playlist... (Isso pode demorar um momento!)")
        
        songs_list, playlist_title = await extract_playlist_songs(search)
        
        if not songs_list:
            await ctx.send("Desculpe, não consegui carregar essa playlist ou ela está vazia.")
            return
        
        # Adiciona todas as músicas da lista na fila
        queues[guild_id].extend(songs_list)
        await ctx.send(f"✅ Adicionadas **{len(songs_list)}** músicas da playlist **'{playlist_title}'** à fila.")

    else:
        # É MÚSICA ÚNICA (BUSCA OU LINK DIRETO)
        await ctx.send(f"🔎 Procurando por: **{search}**...")
        
        url, title = await search_youtube(search)
        
        if not url:
            await ctx.send("Desculpe, não consegui encontrar essa música.")
            return

        song = {'url': url, 'title': title}
        queues[guild_id].append(song)
        await ctx.send(f"✅ Adicionado à fila: **{title}**")

    # 4. COMEÇAR A TOCAR (se não estiver tocando)
    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)


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
        ctx.voice_client.stop() # Isso vai acionar o 'after' na função play_next
        await ctx.send("⏭️ Música pulada.")
    else:
        await ctx.send("Não há música tocando para pular.")

@bot.command(name='stop', aliases=['parar'], help="Para a música e limpa a fila")
async def stop(ctx):
    guild_id = ctx.guild.id
    
    if guild_id in queues:
        queues[guild_id] = []
        
    current_song[guild_id] = None
    
    if ctx.voice_client:
        ctx.voice_client.stop()
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

    queue_list = []
    # Limita a exibição para as próximas 10 músicas
    for i, song in enumerate(queues[guild_id][:10]):
        queue_list.append(f"{i + 1}. {song['title']}")

    now_playing = current_song.get(guild_id)
    if not now_playing:
        now_playing = "Nada"

    embed = discord.Embed(
        title="Fila de Músicas",
        color=discord.Color.blue()
    )
    embed.add_field(name="Tocando Agora", value=f"**{now_playing}**", inline=False)
    
    if queue_list:
        embed.add_field(name="Próximas", value="\n".join(queue_list), inline=False)
        if len(queues[guild_id]) > 10:
            embed.set_footer(text=f"e mais {len(queues[guild_id]) - 10}...")
            
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
bot.run("DISCORD_TOKEN")
