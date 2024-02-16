import gradio as gr
import os, shutil
import subprocess
from datetime import datetime
os.environ["rmvpe_root"] = "assets/rmvpe"
os.environ['index_root']="logs"
os.environ['weight_root']="assets/weights"

def convert(audio_picker,model_picker):
    gr.Warning("Your audio is being converted. Please wait.")
    now = datetime.now().strftime("%d%m%Y%H%M%S")
    command = [
        "python",
        "tools/infer_cli.py",
        "--f0up_key", "0",
        "--input_path", f"audios/{audio_picker}",
        "--index_path", f"logs/{model_picker}/*.index",
        "--f0method", "rmvpe",
        "--opt_path", f"audios/cli_output_{now}.wav",
        "--model_name", f"{model_picker}",
        "--index_rate", "0.8",
        "--device", "cpu",
        "--filter_radius", "3",
        "--resample_sr", "0",
        "--rms_mix_rate", "0.21",
        "--protect", "0"
    ]

    try:
        process = subprocess.run(command, check=True)
        print("Script executed successfully.")
        return {"choices":show_available("audios"),"__type__":"update","value":f"cli_output_{now}.wav"},f"audios/cli_output_{now}.wav"
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return {"choices":show_available("audios"),"__type__":"update"}, None

assets_folder = "assets"
if not os.path.exists(assets_folder):
    os.makedirs(assets_folder)
files = {
    "rmvpe/rmvpe.pt":"https://huggingface.co/Rejekts/project/resolve/main/rmvpe.pt",
    "hubert/hubert_base.pt":"https://huggingface.co/Rejekts/project/resolve/main/hubert_base.pt",
    "pretrained_v2/D40k.pth":"https://huggingface.co/Rejekts/project/resolve/main/D40k.pth",
    "pretrained_v2/G40k.pth":"https://huggingface.co/Rejekts/project/resolve/main/G40k.pth",
    "pretrained_v2/f0D40k.pth":"https://huggingface.co/Rejekts/project/resolve/main/f0D40k.pth",
    "pretrained_v2/f0G40k.pth":"https://huggingface.co/Rejekts/project/resolve/main/f0G40k.pth"
}
for file, link in files.items():
    file_path = os.path.join(assets_folder, file)
    if not os.path.exists(file_path):
        try:
            subprocess.run(['wget', link, '-O', file_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error downloading {file}: {e}")
            
def download_from_url(url, model):
    if url == '':
        return "URL cannot be left empty.", {"choices":show_available("assets/weights"),"__type__":"update"}
    if model =='':
        return "You need to name your model. For example: My-Model", {"choices":show_available("assets/weights"),"__type__":"update"}
    url = url.strip()
    zip_dirs = ["zips", "unzips"]
    for directory in zip_dirs:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    os.makedirs("zips", exist_ok=True)
    os.makedirs("unzips", exist_ok=True)
    zipfile = model + '.zip'
    zipfile_path = './zips/' + zipfile
    try:
        if "drive.google.com" in url:
            subprocess.run(["gdown", url, "--fuzzy", "-O", zipfile_path])
        elif "mega.nz" in url:
            m = Mega()
            m.download_url(url, './zips')
        else:
            subprocess.run(["wget", url, "-O", zipfile_path])
        for filename in os.listdir("./zips"):
            if filename.endswith(".zip"):
                zipfile_path = os.path.join("./zips/",filename)
                shutil.unpack_archive(zipfile_path, "./unzips", 'zip')
            else:
                return "No zipfile found.", {"choices":show_available("assets/weights"),"__type__":"update"}
        for root, dirs, files in os.walk('./unzips'):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(".index"):
                    os.mkdir(f'./logs/{model}')
                    shutil.copy2(file_path,f'./logs/{model}')
                elif "G_" not in file and "D_" not in file and file.endswith(".pth"):
                    shutil.copy(file_path,f'./assets/weights/{model}.pth')
        shutil.rmtree("zips")
        shutil.rmtree("unzips")
        return "Success.", {"choices":show_available("assets/weights"),"__type__":"update"}
    except:
        return "There's been an error.", {"choices":show_available("assets/weights"),"__type__":"update"}
            
def show_available(filepath,format=None):
    if format:
        print(f"Format: {format}")
        files = []
        for file in os.listdir(filepath):
            if file.endswith(format):
                print(f"Matches format: {file}")
                files.append(file)
            else:
                print(f"Does not match format: {file}")
        print(f"Matches: {files}")
        return files
    return os.listdir(filepath)
  
def upload_file(file):
    audio_formats = ['.wav', '.mp3', '.ogg', '.flac', '.aac']
    print(file)
    try:
        _, ext = os.path.splitext(file.name)
        filename = os.path.basename(file.name)
        file_path = file.name
    except AttributeError:
        _, ext = os.path.splitext(file)
        filename = os.path.basename(file)
        file_path = file
    if ext.lower() in audio_formats:
        if os.path.exists(f'audios/{filename}'): 
            os.remove(f'audios/{filename}')
        shutil.move(file_path,'audios')
    else:
        gr.Warning('File incompatible')
    return {"choices":show_available('audios'),"__type__": "update","value":filename}

def refresh():
    return {"choices":show_available("audios"),"__type__": "update"},{"choices":show_available("assets/weights",".pth"),"__type__": "update"}

def update_audio_player(choice):
    return os.path.join("audios",choice)

with gr.Blocks() as app:
    with gr.Row():
        with gr.Column():
            with gr.Tabs():
                with gr.TabItem("1.Choose a voice model:"):
                    model_picker = gr.Dropdown(label="",choices=show_available('assets/weights','.pth'),value='',interactive=True)
                with gr.TabItem("(Or download a model here)"):
                    with gr.Row():
                        url = gr.Textbox(label="Paste the URL here:",value="",placeholder="(i.e. https://huggingface.co/repo/model/resolve/main/model.zip)")
                    with gr.Row():
                        with gr.Column():
                            model_rename = gr.Textbox(placeholder="My-Model", label="Name your model:",value="")
                        with gr.Column():
                            download_button = gr.Button("Download")
                            download_button.click(fn=download_from_url,inputs=[url,model_rename],outputs=[url,model_picker])
        
    with gr.Row():
        with gr.Tabs():
            with gr.TabItem("2.Choose an audio file:"):
                recorder = gr.Microphone(label="Record audio here...",type='filepath')
                audio_picker = gr.Dropdown(label="",choices=show_available('audios'),value='',interactive=True)
                recorder.stop_recording(upload_file, inputs=[recorder],outputs=[audio_picker])
            with gr.TabItem("(Or upload a new file here)"):
                dropbox = gr.Audio(label="Drop an audio here.",sources=['upload'], type="filepath")
                dropbox.upload(fn=upload_file, inputs=[dropbox],outputs=[audio_picker])
        audio_refresher = gr.Button("Refresh")
        audio_refresher.click(fn=refresh,inputs=[],outputs=[audio_picker,model_picker])
        convert_button = gr.Button("Convert")
    with gr.Row():
        audio_player = gr.Audio()
        audio_picker.change(fn=update_audio_player, inputs=[audio_picker],outputs=[audio_player])
        convert_button.click(convert, inputs=[audio_picker,model_picker],outputs=[audio_picker,audio_player])

app.queue().launch()