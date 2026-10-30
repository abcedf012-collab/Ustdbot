import telebot
from telebot import types

TOKEN = '9205107300:AAH_Cz2l6L0M-EQqirDnGU7dpstLvscR0hU'
ADMIN_ID = 2130773719  # Ton ID Telegram perso

bot = telebot.TeleBot(TOKEN)

# Dictionnaire temporaire pour stocker les choix des clients
user_data = {}

# 1. Démarrage
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_buy = types.InlineKeyboardButton("💰 Buy USDT", callback_data="buy")
    markup.add(btn_buy)
    bot.send_message(message.chat.id, "Welcome! Click below to buy USDT using PayPal, Zelle, or Chime:", reply_markup=markup)

# 2. Choix de la méthode de paiement
@bot.callback_query_handler(func=lambda call: call.data == "buy")
def ask_payment_method(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("PayPal", callback_data="pay_paypal"),
        types.InlineKeyboardButton("Zelle", callback_data="pay_zelle"),
        types.InlineKeyboardButton("Chime", callback_data="pay_chime")
    )
    bot.edit_message_text("Choose your payment method:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# 3. Demander le montant en dollars ($)
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def ask_amount(call):
    method = call.data.split("_")[1].upper()
    user_data[call.from_user.id] = {"method": method}
    
    bot.edit_message_text(
        f"You selected **{method}**.\n\n"
        f"Please type the amount in USD you want to send (e.g., `50` or `100`):",
        call.message.chat.id, 
        call.message.message_id, 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(call.message, calculate_and_show)

# 4. Calculer les frais (6.5%) et afficher le résultat
def calculate_and_show(message):
    try:
        usd_amount = float(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount. Please type numbers only (e.g., 50). Type /start to restart.")
        return
    
    user_id = message.from_user.id
    method = user_data.get(user_id, {}).get("method", "Payment")
    
    # Calcul des 6.5% de frais
    fee_percentage = 0.065
    fee_amount = usd_amount * fee_percentage
    net_usd = usd_amount - fee_amount
    
    # USDT à recevoir
    usdt_to_receive = net_usd 
    
    # Enregistrer les montants
    user_data[user_id]["usd"] = usd_amount
    user_data[user_id]["usdt"] = usdt_to_receive

    # Demander l'adresse USDT du client
    msg = (
        f"📊 **Calculation Summary:**\n"
        f"• You send: **${usd_amount:.2f} USD**\n"
        f"• Fees (6.5%): **-${fee_amount:.2f} USD**\n"
        f"• You will receive: **{usdt_to_receive:.2f} USDT**\n\n"
        f"Now, please reply with your **USDT Wallet Address (TRC20 / BEP20)**:"
    )
    
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(message, get_wallet_address)

# 5. Demander l'adresse et afficher tes informations personnelles de paiement
def get_wallet_address(message):
    user_id = message.from_user.id
    wallet = message.text
    user_data[user_id]["wallet"] = wallet
    
    data = user_data[user_id]
    method = data["method"]
    usd = data["usd"]
    usdt = data["usdt"]
    
    # --- TES INFORMATIONS DE PAIEMENT ---
    paypal_info = "levonkosy@gmail.com"
    zelle_info = "+1"  # Pense à compléter ton numéro si besoin après le +1
    chime_info = "@chimeiu"
    # -----------------------------------
    
    # Sélection automatique selon le choix du client
    if method == "PAYPAL":
        my_payment_account = paypal_info
    elif method == "ZELLE":
        my_payment_account = zelle_info
    else:
        my_payment_account = chime_info

    # Instructions finales affichées au client
    payment_instructions = (
        f"🎯 **Final Step!**\n\n"
        f"Send **${usd:.2f}** via **{method}** to our account:\n"
        f"`{my_payment_account}`\n\n"
        f"You will receive **{usdt:.2f} USDT** at your address:\n"
        f"`{wallet}`\n\n"
        f"Once you have sent the money, click the button below:"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ I Have Paid", callback_data="final_paid"))
    
    bot.send_message(message.chat.id, payment_instructions, parse_mode="Markdown", reply_markup=markup)

# 6. Alerte Admin finale
@bot.callback_query_handler(func=lambda call: call.data == "final_paid")
def final_paid_action(call):
    user = call.from_user
    data = user_data.get(user.id, {})
    
    # Message rassurant pour le client
    bot.edit_message_text(
        "⏳ **Payment Submitted!**\n\n"
        "Please wait **between 20 minutes and 3 hours** while we check your payment and release your crypto.",
        call.message.chat.id, 
        call.message.message_id, 
        parse_mode="Markdown"
    )
    
    # Alerte pour toi (Admin) avec tous les détails précis
    admin_msg = (
        f"🚨 **NEW PAID ORDER !**\n\n"
        f"👤 Customer: @{user.username} (ID: `{user.id}`)\n"
        f"💳 Method: {data.get('method')}\n"
        f"💵 Client sends: ${data.get('usd')}\n"
        f"🪙 USDT to send: **{data.get('usdt'):.2f} USDT**\n"
        f"📥 Wallet Address: `{data.get('wallet')}`\n\n"
        f"Check your account and send the crypto manually!"
    )
    
    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")

# Lancement du bot
print("Bot is running...")
bot.infinity_polling()
