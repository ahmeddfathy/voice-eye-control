import speech_recognition as sr
import threading
from gtts import gTTS
import io
import pygame
import tkinter as tk
from tkinter import scrolledtext

pygame.mixer.init()

listening = False
language = "ar-EG"  # اللغة الافتراضية

def play_audio_feedback(text):
    """تشغيل صوت لتأكيد الأوامر."""
    audio_buffer = io.BytesIO()
    tts = gTTS(text=text, lang='ar')
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    pygame.mixer.music.load(audio_buffer, "mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass

def execute_voice_command(command):
    """تنفيذ الأوامر الصوتية."""
    global listening
    if "بدء الاستماع" in command:
        start_listening_by_voice()
    elif "وقف الاستماع" in command:
        stop_listening_by_voice()
    elif "سلكت" in command:
        select_all_text()
    elif "كوبي" in command:
        copy_text()
    elif "كت" in command:
        cut_text()
    else:
        write_text(command)

def write_text(command):
    """كتابة النص المنطوق."""
    display_text.insert(tk.END, command + "\n")
    display_text.see(tk.END)
    play_audio_feedback("تم كتابة النص")

def select_all_text():
    """تحديد كل النصوص."""
    display_text.tag_add("sel", "1.0", "end")
    display_text.focus()
    play_audio_feedback("تم تحديد كل النصوص")

def copy_text():
    """نسخ النصوص المحددة."""
    try:
        app.clipboard_clear()
        app.clipboard_append(display_text.get("sel.first", "sel.last"))
        play_audio_feedback("تم نسخ النصوص")
    except tk.TclError:
        play_audio_feedback("لم يتم تحديد نصوص للنسخ")

def cut_text():
    """قص النصوص المحددة."""
    try:
        app.clipboard_clear()
        app.clipboard_append(display_text.get("sel.first", "sel.last"))
        display_text.delete("sel.first", "sel.last")
        play_audio_feedback("تم قص النصوص")
    except tk.TclError:
        play_audio_feedback("لم يتم تحديد نصوص للقص")

def voice_recognition_loop():
    """حلقة الاستماع للصوت وتحويله إلى نص."""
    global listening
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            if listening:
                try:
                    audio = recognizer.listen(source, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio, language=language)
                    execute_voice_command(text)
                except sr.UnknownValueError:
                    play_audio_feedback("لم يتم التعرف على الكلام")
                except sr.RequestError:
                    play_audio_feedback("خطأ في الخدمة")
                except Exception as e:
                    play_audio_feedback("حدث خطأ غير متوقع")

def start_listening():
    """بدء الاستماع."""
    global listening
    listening = True
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    play_audio_feedback("تم تشغيل الاستماع")

def start_listening_by_voice():
    """بدء الاستماع باستخدام الصوت."""
    global listening
    listening = True
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    play_audio_feedback("تم تشغيل الاستماع")

def stop_listening():
    """إيقاف الاستماع."""
    global listening
    listening = False
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    play_audio_feedback("تم إيقاف الاستماع")

def stop_listening_by_voice():
    """إيقاف الاستماع باستخدام الصوت."""
    global listening
    listening = False
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    play_audio_feedback("تم إيقاف الاستماع")

# واجهة المستخدم
app = tk.Tk()
app.title("تحويل الصوت إلى نص")
app.geometry("600x400")

# منطقة عرض النصوص
display_text = scrolledtext.ScrolledText(app, wrap=tk.WORD, width=60, height=15, font=("Arial", 12))
display_text.pack(pady=10)

# أزرار التحكم
control_frame = tk.Frame(app)
control_frame.pack(pady=10)

start_button = tk.Button(control_frame, text="ابدأ الاستماع", command=start_listening, width=20, bg="green", fg="white")
start_button.grid(row=0, column=0, padx=5)

stop_button = tk.Button(control_frame, text="أوقف الاستماع", command=stop_listening, width=20, bg="red", fg="white", state=tk.DISABLED)
stop_button.grid(row=0, column=1, padx=5)

# حلقة الاستماع
app.after(100, lambda: threading.Thread(target=voice_recognition_loop, daemon=True).start())
app.mainloop()
