import os
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from ttkthemes import ThemedTk
import logging
from common import (transcribe_audio, split_audio, summarize_as_thesis, 
                    synthesize_summaries, excerpt_text, uber_synthesize, save_to_file)

def gui_transcribe_audio():
    file_path = filedialog.askopenfilename(title="Select Audio File", filetypes=[("M4A Files", "*.m4a"), ("MP3 Files", "*.mp3")])
    if not file_path:
        return

    user_prompt = simpledialog.askstring("User Prompt", "Enter a prompt (or cancel to skip):")
    if not user_prompt:
        user_prompt = None

    chunks = split_audio(file_path)
    individual_summaries = []
    combined_transcripts = []

    for idx, chunk in enumerate(chunks):
        temp_file = f"temp_chunk_{idx}.m4a"
        chunk.export(temp_file, format="mp4", codec="aac")
        transcript = transcribe_audio(temp_file, user_prompt)
        os.remove(temp_file)

        if transcript:
            combined_transcripts.append(transcript)
            summary = summarize_as_thesis(transcript)
            if summary:
                individual_summaries.append(summary)
            else:
                logging.warning(f"Summary generation failed for chunk {idx}.")
        else:
            logging.warning(f"Transcription failed for chunk {idx}.")

    full_transcription = ' '.join(combined_transcripts).replace(' .', '.')
    excerpted_transcription = excerpt_text(full_transcription)

    result_text.insert(tk.END, "Transcripts:\n")
    result_text.insert(tk.END, full_transcription)
    result_text.insert(tk.END, "\n\n")

    final_summary = synthesize_summaries(individual_summaries)
    if final_summary:
        #result_text.insert(tk.END, "Final Synthesis:\n")
        #result_text.insert(tk.END, final_summary)
        #result_text.insert(tk.END, "\n\n")

        uber_final_summary = uber_synthesize(excerpted_transcription, final_summary)
        if uber_final_summary:
            result_text.insert(tk.END, "Synthesis:\n")
            result_text.insert(tk.END, uber_final_summary)
            result_text.insert(tk.END, "\n\n")
            save_to_file(full_transcription, uber_final_summary)
        else:
            logging.warning("Failed to generate an über-final synthesis.")
    else:
        logging.warning("Failed to generate a final synthesis.")

# Functions for button hover effects
def on_enter(e):
    select_button['background'] = '#fd0054'

def on_leave(e):
    select_button['background'] = '#00dbcd'

# Main application window
app = ThemedTk(theme="equilux")
app.title("SUMMA TRANSSCRIPTUS")
app.config(bg='#FF073A')
app.geometry('800x600')

# Optionally, set an application icon
app.iconbitmap('icon.ico')

# Font Styling
font_style = ("Roboto", 25)
font_small = ("Roboto", 15)

# Main frame to hold all widgets
main_frame = ttk.Frame(app)
main_frame.pack(pady=20, padx=20, expand=True, fill=tk.BOTH)

# Button with hover effects
select_button = tk.Button(main_frame, 
                          text="SUMMA!", 
                          command=gui_transcribe_audio,
                          bg='#39FF14',
                          fg='#fd0054',
                          font=font_style)

select_button.bind("<Enter>", on_enter)
select_button.bind("<Leave>", on_leave)
select_button.pack(pady=20)

# Text widget with scrollbar
scrollbar = ttk.Scrollbar(main_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

result_text = tk.Text(main_frame, 
                      height=20, 
                      width=80, 
                      bg='#3a1c71',
                      fg='#39FF14',
                      font=font_small,
                      yscrollcommand=scrollbar.set)
result_text.pack(pady=20, padx=20, expand=True, fill=tk.BOTH)

scrollbar.config(command=result_text.yview)

app.mainloop()