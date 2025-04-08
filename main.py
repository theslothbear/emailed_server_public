from flask import Flask, request, render_template, render_template_string

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/keys")
def keys():
    return render_template('keys.html')

@app.route('/mail')
def mail():
    try:
        from connector import MailConnector
        login, password, imap_server, m_id = request.args.get('l'), request.args.get('p'), request.args.get('i'), request.args.get('mid')
        mail = MailConnector(login, password, imap_server)
        if mail.connect() == True:
            mail_text = mail.get_mail_text2(str(m_id))
            sender, header, plain_text, html_text = mail_text['sender'], mail_text['header'], mail_text['plain'], mail_text['html']
            if html_text:
                text = html_text
            else:
                text = plain_text
            return render_template_string(f'<!DOCTYPE html><html><head><script src="https://telegram.org/js/telegram-web-app.js?56"></script><script>window.Telegram.WebApp.headerColor = "#331A00";window.Telegram.WebApp.backgroundColor = "#FFF5E6";window.Telegram.WebApp.MainButton.isVisible = true;window.Telegram.WebApp.MainButton.color = "#331A00";window.Telegram.WebApp.MainButton.text = "Полноэкранный режим";window.Telegram.WebApp.MainButton.onClick(() => window.Telegram.WebApp.isFullscreen ? window.Telegram.WebApp.exitFullscreen() : window.Telegram.WebApp.requestFullscreen());window.Telegram.WebApp.ready();</script><link rel="stylesheet" type="text/css" href="/static/css/mail.css"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>E-Mailed</title></head><body><div class="email-header"><h1 class="email-subject">✉ {header}</h1><p class="email-sender">👤 <a href="mailto:{sender}">{sender}</a></p></div><div id="mail">{text}</div></body></html>')
        else:
            return f'Неверный логин или пароль: {mail.connect()}'
    except Exception as e:
        return f'Произошла ошибка: {str(e)}'

@app.route('/retell')
def retell():
    try:
        from connector import MailConnector
        login, password, imap_server, m_id, key = request.args.get('l'), request.args.get('p'), request.args.get('i'), request.args.get('mid'), request.args.get('key')
        mail = MailConnector(login, password, imap_server)
        if mail.connect() == True:
            mail_text = mail.get_mail_text2(str(m_id))
            sender, header, plain_text, html_text = mail_text['sender'], mail_text['header'], mail_text['plain'], mail_text['html']
            if plain_text:
                text = BeautifulSoup(plain_text, features="lxml").get_text()
            else:
                text = mail.get_text_from_html(html_text)
            try:
                from gigachat import GigaChat
                model = GigaChat(
                   credentials=key,
                   scope="GIGACHAT_API_PERS",
                   model="GigaChat",
                   verify_ssl_certs=False,
                )
                if len(text) > 30000:
                    text = text[:30000]
                response = model.chat(f'Перескажи письмо в нескольких предложениях от имени отправителя письма": {text}')
                r = response.choices[0].message.content
                return render_template_string(f'<!DOCTYPE html><html><head><script src="https://telegram.org/js/telegram-web-app.js?56"></script><script>window.onload = function(){{window.Telegram.WebApp.headerColor = "#331A00";window.Telegram.WebApp.backgroundColor = "#331A00";window.Telegram.WebApp.MainButton.isVisible = true;window.Telegram.WebApp.MainButton.color = "#331A00";window.Telegram.WebApp.MainButton.text = "Полноэкранный режим";window.Telegram.WebApp.MainButton.onClick(() => window.Telegram.WebApp.isFullscreen ? window.Telegram.WebApp.exitFullscreen() : window.Telegram.WebApp.requestFullscreen());}}</script><link rel="stylesheet" type="text/css" href="/static/css/mail.css"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>E-Mailed</title></head><body><div class="email-header"><h1 class="email-subject">✉ {header}</h1><p class="email-sender">👤 <a href="mailto:{sender}">{sender}</a></p></div><div id="retell">{r}</div></body></html>')
            except Exception as e:
                #return str(e)
                return render_template_string(f'<!DOCTYPE html><html><head><script src="https://telegram.org/js/telegram-web-app.js?56"></script><script>window.onload = function(){{window.Telegram.WebApp.headerColor = "#331A00";window.Telegram.WebApp.backgroundColor = "#331A00";window.Telegram.WebApp.MainButton.isVisible = true;window.Telegram.WebApp.MainButton.color = "#331A00";window.Telegram.WebApp.MainButton.text = "Полноэкранный режим";window.Telegram.WebApp.MainButton.onClick(() => window.Telegram.WebApp.isFullscreen ? window.Telegram.WebApp.exitFullscreen() : window.Telegram.WebApp.requestFullscreen());}}</script><link rel="stylesheet" type="text/css" href="/static/css/mail.css"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>E-Mailed</title></head><body><div id="mail">Не удалось пересказать текст письма: токен GigaChat недействителен</div></body></html>')
        else:
            return f'Неверный логин или пароль: {mail.connect()}'
    except Exception as e:
        return f'Произошла ошибка: {str(e)}'

@app.route('/tgcheck_data')
def check_data():
    data = request.url.split('?')[-1]
    token = ''

    import urllib.parse
    import hashlib
    import hmac

    # Transforms Telegram.WebApp.initData string into object
    def transform_init_data(init_data: str):
        res = dict(urllib.parse.parse_qs(init_data))
        for key, value in res.items():
            res[key] = value[0]
        return res


    # Accepts init data object and bot token
    def validate(data: dict, bot_token: str):
        check_string = "\n".join(
            sorted(f"{key}={value}" for key, value in data.items() if key != "hash"))
        #print("computed_string", check_string)
        secret = hmac.new(key=b'WebAppData', msg=bot_token.encode(),
                          digestmod=hashlib.sha256)
        signature = hmac.new(key=secret.digest(),
                             msg=check_string.encode(), digestmod=hashlib.sha256)

        #print("original hash:", data['hash'])
        #print("computed hash:", signature.hexdigest())

        return hmac.compare_digest(data['hash'], signature.hexdigest())

    data = transform_init_data(data)
    return f'{validate(data, token)}'
    
@app.route('/addmail')
def add_mail():
    return render_template('addmail.html')

@app.route('/parse')
def parse():
    login, password, imap, m_id = request.args.get('login'), request.args.get('pass'), request.args.get('imap'), request.args.get('mail_id')
    return render_template('parse.html', login = login)

@app.route('/change_token')
def change_token():
    return render_template('change_token.html')

app.run(host='0.0.0.0',port=1080)
