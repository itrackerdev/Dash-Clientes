# data_loader.py

import io
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def download_file_from_gdrive():
    try:
        # Recupera as credenciais a partir dos secrets
        credentials_info = st.secrets["google"]
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, 
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        file_id = "1Bphi7lChPqh12kAStpupXJmCbwcdImKo"  # Ajuste o ID conforme necessário
        st.sidebar.info("Baixando arquivo real do Google Sheets...")
        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        while not done:
            status, done = downloader.next_chunk()
            progress = int(status.progress() * 100)
            progress_bar.progress(progress)
            status_text.text(f"Download: {progress}%")
        status_text.text("Download concluído!")
        progress_bar.empty()
        file.seek(0)
        df = pd.read_excel(file, engine='openpyxl')
        st.sidebar.success("Arquivo carregado com sucesso!")
        return df
    except Exception as e:
        st.sidebar.error(f"Erro ao acessar o Google Drive: {str(e)}")
        return None

def validate_dataframe(df):
    required_cols = ['Cliente', 'MÊS', 'BUDGET', 'Importação', 'Exportação', 'Cabotagem', 'Quantidade_iTRACKER']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Colunas ausentes: {', '.join(missing)}")
        st.stop()
    return df
