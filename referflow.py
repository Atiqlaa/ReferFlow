"""
PROJECT: CutPrice Exchange Bot
DESCRIPTION: Telegram Bot untuk pertukaran klik link antara pengguna.
"""

import logging
import os
import sqlite3
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
load_dotenv(r"Path to token file")
TOKEN = os.getenv("BOT_TOKEN")

# --- GLOBAL VARIABLES (Memory Storage) ---
waiting_list = []  # Menyimpan ID user yang sedang mencari partner
active_pairs = {}  # Menyimpan pasangan aktif {user_id: partner_id}

# ==========================================
# DATABASE FUNCTIONS
# ==========================================

def init_db():
    """Membina table users jika belum wujud dalam database."""
    conn = sqlite3.connect("datauser.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        userid INTEGER PRIMARY KEY,
                        username TEXT,
                        firstname TEXT,
                        status TEXT,
                        tried INTEGER,
                        total_stars INTEGER DEFAULT 0,
                        total_sessions INTEGER DEFAULT 0,
                        lastseen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_user(userid, username, firstname, status="Non-Active", tried=None, ):
    """Menambah atau mengemaskini maklumat profil user."""
    conn = sqlite3.connect('datauser.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT OR IGNORE INTO users (userid, username, firstname, status, tried) 
                      VALUES (?, ?, ?, ?, ?)''', (userid, username, firstname, status, tried))
    conn.commit()
    conn.close()

def connect(userid, status):
    """Mengemaskini status ketersediaan user (Active/Non-Active)."""
    conn = sqlite3.connect('datauser.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = ? WHERE userid = ?', (status, userid))
    conn.commit()
    conn.close()

def tried(userid, tried_val):
    """Mengemaskini status 'tried' (1 = sudah hantar link, None = sedia hantar)."""
    conn = sqlite3.connect('datauser.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET tried = ? WHERE userid = ?', (tried_val, userid))
    conn.commit()
    conn.close()

# ==========================================
# COMMAND HANDLERS
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fungsi permulaan /start - Daftar user & tunjuk butang cari."""
    user = update.effective_user
    save_user(user.id, user.username, user.first_name, None)
    
    keyboard = [[InlineKeyboardButton("Cari Partner 🔍", callback_data='find_partner')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Selamat datang {user.first_name}! Klik tombol di bawah untuk cari partner klik link.", reply_markup=reply_markup)

async def lihat_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fungsi Admin untuk melihat senarai semua user dalam DB."""
    conn = sqlite3.connect('datauser.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    conn.close()

    text = "Senarai User Terkumpul:\n\n"
    for row in rows:
        text += f"ID: {row[0]} | User: @{row[1]} | Nama: {row[2]}\n | Status: {row[3]}\n | Total Stars: {row[5]}\n"
    await update.message.reply_text(text)

# ==========================================
# CALLBACK QUERY HANDLER (Buttons)
# ==========================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menguruskan semua interaksi butang Inline Keyboard."""
    query = update.callback_query
    user_id = query.from_user.id
    partner_id = active_pairs.get(user_id)
    await query.answer()

    # --- LOGIK CANCEL ---
    if query.data == 'cancel':
        if user_id in waiting_list:
            waiting_list.remove(user_id)
            await query.edit_message_text("Carian partner dibatalkan.")
            return

        if partner_id:
            # Putuskan hubungan dalam memori
            active_pairs.pop(user_id, None)
            active_pairs.pop(partner_id, None)

            # Reset Database
            connect(user_id, "Non-Active")
            connect(partner_id, "Non-Active")
            tried(user_id, None)
            tried(partner_id, None)

            await query.edit_message_text("Sesi dibatalkan. Anda boleh cari partner baru.")
            try:
                await context.bot.send_message(partner_id, "Partner anda telah membatalkan sesi.")
            except: pass
        else:
            await query.edit_message_text("Anda tidak mempunyai sesi aktif.")

    # --- LOGIK FIND PARTNER ---
    elif query.data == 'find_partner':
        if user_id in waiting_list:
            await query.answer("Sabar, tengah cari partner...", show_alert=True)
            return

        if waiting_list: #Jika Org yg tekan find skrg ternyata dah ada org tunggu kat waiting list
            partner_id = waiting_list.pop(0)
            active_pairs[user_id] = partner_id
            active_pairs[partner_id] = user_id
            
            connect(user_id, "Active")
            connect(partner_id, "Active")
            
            conn = sqlite3.connect('datauser.db')
            cursor = conn.cursor()
            
            # Ambil data Partner (orang yang dalam waiting list)
            cursor.execute('SELECT total_stars, total_sessions FROM users WHERE userid = ?', (partner_id,))
            p_data = cursor.fetchone()
            
            # Ambil data Diri Sendiri (user yang baru tekan butang)
            cursor.execute('SELECT total_stars, total_sessions FROM users WHERE userid = ?', (user_id,))
            u_data = cursor.fetchone()
            conn.close()

            # Sediakan info untuk dipaparkan (Default 0 kalau data tak jumpa)
            p_stars, p_sess = p_data if p_data else (0, 0)
            u_stars, u_sess = u_data if u_data else (0, 0)
            
            msg_for_me = (
                "🤝 **Partner Dijumpai!**\n\n"
                f"👤 **Partner:** Dirahsiakan!\n"
                f"⭐ **Bintang:** {p_stars}\n"
                f"🔄 **Sesi Selesai:** {p_sess}\n\n"
                "⚠️ *Jika reputasi partner meragukan (Sesi tinggi tapi bintang 0), anda boleh tekan Putuskan Sesi.*"
            )
            
            msg_for_partner = (
                "🤝 **Partner Dijumpai!**\n\n"
                f"👤 **Partner:** Dirahsiakan!\n"
                f"⭐ **Bintang:** {u_stars}\n"
                f"🔄 **Sesi Selesai:** {u_sess}\n\n"
                "Sila hantar link anda untuk mulakan pertukaran."
            )
            
            try:
                keyboard=[[InlineKeyboardButton('Putuskan Sesi ❌', callback_data='cancel')]]
                reply_markup=InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(msg_for_me, reply_markup=reply_markup, parse_mode='Markdown')
                await context.bot.send_message(partner_id, msg_for_partner, reply_markup=reply_markup, parse_mode='Markdown')
            except:
                pass
        else:
            waiting_list.append(user_id)
            keyboard = [[InlineKeyboardButton('Cancel ❌', callback_data='cancel')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Mencari partner... Sila tunggu.", reply_markup=reply_markup)

    # --- LOGIK SELESAI TEKAN (DONE) ---
    elif query.data.startswith('doneclick_'):
        p_id = int(query.data.split('_')[1])
        keyboard= [[InlineKeyboardButton('⭐', callback_data=f'star_{user_id}')]]
        reply_markup=InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(p_id, "✅ Partner anda kata dia dah tekan link anda!")
        await context.bot.send_message(p_id, "Bagi bintang ke partner?" ,reply_markup=reply_markup)
        await query.edit_message_text("Terima kasih! Notifikasi sudah dihantar kepada partner.")
        conn = sqlite3.connect('datauser.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET total_sessions = total_sessions + 1 WHERE userid = ?", (user_id,))
        conn.commit()
        conn.close()

        context.user_data['done'] = True
        partner_data = context.application.user_data.get(p_id, {})
        partner_done = partner_data.get('done', False)

        if partner_done:
            # JIKA KEDUA-DUA DAH TEKAN: Tutup Sesi Total
            active_pairs.pop(user_id, None)
            active_pairs.pop(p_id, None)

            # Reset status DB untuk kedua-dua
            connect(user_id, "Non-Active")
            connect(p_id, "Non-Active")
            tried(user_id, None)
            tried(p_id, None)

            # Kosongkan penanda 'done' dalam memori
            context.user_data.pop('done', None)
            if p_id in context.application.user_data:
                context.application.user_data[p_id].pop('done', None)                             
            await query.edit_message_text("Sesi Tamat! Kedua-dua pihak telah selesai. Terima kasih.")
            await context.bot.send_message(p_id, "Sesi Tamat! Partner anda juga telah selesai tekan link anda.")
        else:
            # JIKA HANYA SEORANG DAH TEKAN: Biarkan sesi aktif
            await query.edit_message_text("Terima kasih! Menunggu partner tekan link anda pula sebelum sesi ditutup.")

    # BAGI BINTANG
    elif query.data.startswith('star_'):
        target_id = query.data.split('_')[1]
        conn = sqlite3.connect('datauser.db')
        cursor = conn.cursor()
        cursor.execute('''UPDATE users SET total_stars = total_stars + 1 WHERE userid = ?''', (target_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text("Terima kasih! 1 Bintang ⭐ telah diberikan kepada partner anda.")
# ==========================================
# MESSAGE HANDLER (Link Exchange)
# ==========================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menguruskan penghantaran link antara partner yang aktif."""
    user_id = update.message.from_user.id
    partner_id = active_pairs.get(user_id)
    
    if not partner_id:
        await update.message.reply_text("Cari partner dulu sebelum hantar link.")
        return

    # Check status 'tried' dalam DB
    conn = sqlite3.connect('datauser.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tried FROM users WHERE userid = ?', (user_id,))
    res_u = cursor.fetchone()
    pu = res_u[0] if res_u else None
    conn.close()

    if pu == 1:
        await update.message.reply_text("Anda sudah hantar link. Sila tunggu partner tekan ✅.")
        return

    # Hantar link ke partner
    keyboard = [[InlineKeyboardButton("Dah Tekan ✅", callback_data=f'doneclick_{user_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(partner_id, f"Link dari partner:\n{update.message.text}", reply_markup=reply_markup)
        tried(user_id, 1) # Set status sudah mencuba
        await update.message.reply_text("Link dihantar ke partner. Tunggu dia tekan.")
    except Exception as e:
        await update.message.reply_text("Gagal menghantar link. Partner mungkin sudah block bot.")

# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    # Register Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cari", lihat_data))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("Bot sedang berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
    