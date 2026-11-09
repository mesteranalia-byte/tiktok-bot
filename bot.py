import http.server
import os
import socketserver
import threading
import telebot
import yt_dlp

PORT = int(os.environ.get('PORT', 10000))


class SimpleHandler(http.server.BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b'Bot de Telegram Activo y Funcionando!')


def run_web_server():
  with socketserver.TCPServer(('', PORT), SimpleHandler) as httpd:
    httpd.serve_forever()


server_thread = threading.Thread(target=run_web_server, daemon=True)
server_thread.start()

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)


def download_tiktok_live(chat_id, username_or_url):
  if not username_or_url.startswith('http'):
    clean_user = username_or_url.replace('@', '').strip()
    url = f'https://www.tiktok.com/@{clean_user}/live'
  else:
    url = username_or_url

  bot.send_message(
      chat_id,
      f'🔍 *Verificando transmisión en vivo para:* `{username_or_url}`...',
      parse_mode='Markdown',
  )
  output_template = f'live_download_{chat_id}.%(ext)s'
  ydl_opts = {
      'format': 'best',
      'outtmpl': output_template,
      'noplaylist': True,
      'socket_timeout': 30,
      'hls_prefer_native': True,
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      bot.send_message(
          chat_id,
          '🔴 *¡Directo detectado!* Grabando en máxima calidad HD...',
          parse_mode='Markdown',
      )
      info = ydl.extract_info(url, download=True)
      filename = ydl.prepare_filename(info)

    bot.send_message(
        chat_id,
        '✅ *Grabación finalizada.* Enviando archivo...',
        parse_mode='Markdown',
    )

    if os.path.exists(filename):
      file_size_mb = os.path.getsize(filename) / (1024 * 1024)
      if file_size_mb > 50:
        bot.send_message(
            chat_id,
            f'⚠️ El archivo pesa *{file_size_mb:.2f} MB* (supera el límite de'
            ' 50MB de Telegram). Está guardado en el servidor temporal.',
        )
      else:
        bot.send_document(
            chat_id,
            open(filename, 'rb'),
            caption='🎥 *Aquí tienes tu TikTok Live grabado en HD.*',
            parse_mode='Markdown',
        )
        os.remove(filename)
    else:
      bot.send_message(
          chat_id, '❌ No se encontró el archivo de video procesado.'
      )

  except Exception as e:
    bot.send_message(
        chat_id,
        f'❌ *Error al grabar el directo:*\n`{str(e)}`\n\n_Asegúrate de que el'
        ' usuario esté transmitiendo ahora mismo._',
        parse_mode='Markdown',
    )


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  bot.reply_to(
      message,
      '🤖 *Bot de TikTok Live en Render activo!*\nUsa `/live'
      ' nombre_de_usuario`',
      parse_mode='Markdown',
  )


@bot.message_handler(commands=['live'])
def handle_live(message):
  parts = message.text.split()
  if len(parts) < 2:
    bot.reply_to(
        message,
        '❌ *Uso incorrecto.*\nEscribe: `/live usuario_tiktok`',
        parse_mode='Markdown',
    )
    return

  thread = threading.Thread(
      target=download_tiktok_live, args=(message.chat.id, parts[1])
  )
  thread.start()


if __name__ == '__main__':
  print('🚀 Bot iniciado en Render...')
  bot.infinity_polling(timeout=60, long_polling_timeout=60)
