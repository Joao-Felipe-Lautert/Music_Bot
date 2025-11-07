# ... (suas importações e configurações iniciais) ...
# ... (FFMPEG_OPTIONS, YTDL_OPTIONS, YTDL_PLAYLIST_OPTIONS estão OK) ...

# Dicionários de estado
queues = {}
current_song = {}

# 2. FUNÇÕES AUXILIARES DE MÚSICA
# -----------------------------------------------------------------------------

async def play_next(ctx):
    """
    Função auxiliar para tocar a próxima música na fila.
    AGORA ELA EXTRAI O STREAM URL NA HORA DE TOCAR.
    """
    guild_id = ctx.guild.id
    if guild_id in queues and queues[guild_id]:
        # 1. Pega os METADADOS da próxima música
        next_song_metadata = queues[guild_id].pop(0)
        watch_url = next_song_metadata['watch_url']
        title = next_song_metadata['title']

        # 2. Extrai o STREAM URL real SÓ AGORA
        stream_url = None
        try:
            # Usamos as opções de MÚSICA ÚNICA para extrair o áudio
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl: 
                info = ydl.extract_info(watch_url, download=False)
                stream_url = info['url']
                title = info['title'] # Pega o título mais recente/correto
        except Exception as e:
            print(f"Erro ao extrair stream URL para {title}: {e}")
            await ctx.send(f"❌ Erro ao tentar tocar: **{title}**. Pulando.")
            # Tenta tocar a próxima da fila
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            return

        if not stream_url:
            await ctx.send(f"❌ Não foi possível obter o link de áudio para: **{title}**. Pulando.")
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            return

        # 3. Cria a fonte de áudio e toca
        source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(
            source, 
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        )
        
        current_song[guild_id] = title
        await ctx.send(f"🎶 Tocando agora: **{title}**")
    else:
        current_song[guild_id] = None
        await ctx.send("Fila terminada.")

async def get_song_metadata(search_query):
    """
    Busca no YouTube (ou link direto) - APENAS MÚSICA ÚNICA.
    Retorna METADADOS (link do youtube e título), NÃO O STREAM URL.
    """
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(search_query, download=False)
            
            if 'entries' in info and info['entries']:
                video = info['entries'][0] # Pega o primeiro resultado da busca
            else:
                video = info # É um link direto

            # Retorna o link da PÁGINA (watch_url), não o stream URL
            return {'watch_url': video['webpage_url'], 'title': video['title']}

        except Exception as e:
            print(f"Erro ao buscar metadados da música: {e}")
            return None

async def extract_playlist_songs(playlist_url):
    """
    Extrai METADADOS de todas as músicas de uma URL de playlist.
    NÃO extrai o stream url, apenas o link do youtube e título.
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
                        # Adiciona o link do youtube (video['url']) e título
                        songs.append({
                            'watch_url': video['url'], 
                            'title': video.get('title', 'Video Desconhecido')
                        })
                        
        except Exception as e:
            print(f"Erro ao carregar playlist: {e}")
            return [], playlist_title

    return songs, playlist_title


# ... (Seu evento on_ready) ...


# 4. COMANDOS DE MÚSICA
# -----------------------------------------------------------------------------

@bot.command(name='play', aliases=['p', 'tocar'], help="Toca uma música ou playlist do YouTube (busca, link de vídeo ou link de playlist)")
async def play(ctx, *, search: str):
    
    # ... (Sua verificação de canal de voz e conexão) ...
    if not ctx.author.voice:
        await ctx.send("Você precisa estar em um canal de voz para usar este comando!")
        return

    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        try:
            await voice_channel.connect()
        except Exception as e:
            await ctx.send(f"Erro ao conectar ao canal de voz: {e}")
            return
    
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []

    is_playlist = "list=" in search and ("youtube.com/" in search or "youtu.be/" in search)

    if is_playlist:
        # É UMA PLAYLIST
        await ctx.send(f"🔎 Carregando metadados da playlist... (Rápido)")
        
        songs_list, playlist_title = await extract_playlist_songs(search)
        
        if not songs_list:
            await ctx.send("Desculpe, não consegui carregar essa playlist ou ela está vazia.")
            return
        
        # Adiciona os METADADOS na fila
        queues[guild_id].extend(songs_list)
        await ctx.send(f"✅ Adicionados **{len(songs_list)}** metadados da playlist **'{playlist_title}'** à fila.")

    else:
        # É MÚSICA ÚNICA (BUSCA OU LINK DIRETO)
        await ctx.send(f"🔎 Procurando por: **{search}**...")
        
        song_metadata = await get_song_metadata(search)
        
        if not song_metadata:
            await ctx.send("Desculpe, não consegui encontrar essa música.")
            return

        # Adiciona os METADADOS na fila
        queues[guild_id].append(song_metadata)
        await ctx.send(f"✅ Adicionado à fila: **{song_metadata['title']}**")

    # 4. COMEÇAR A TOCAR (se não estiver tocando)
    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)


# ... (Seus comandos pause, resume, skip, stop, queue, nowplaying estão OK) ...


# 5. INICIAR O BOT
# -----------------------------------------------------------------------------
# DICA DE SEGURANÇA: Não coloque seu token direto no código!
# Use variáveis de ambiente. No Discloud, você pode configurar "Secrets".
# import os
# bot.run(os.environ.get("DISCORD_TOKEN"))
bot.run("SEU_TOKEN_AQUI") # Substitua pelo seu token ou, melhor, use uma variável de ambiente