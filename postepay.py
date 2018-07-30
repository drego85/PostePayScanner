#!/usr/bin/python3
import sys
import Config
import hashlib
import smtplib
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Inizializzo i LOG
logging.basicConfig(filename="postepay.log",
                    format="%(asctime)s - %(funcName)10s():%(lineno)s - %(levelname)s - %(message)s",
                    level=logging.INFO)

headerdesktop = {"User-Agent": "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
                 "Accept-Language": "it"}
timeoutconnection = 10

movimentiList = []


def send_email(datacontabile, datavaluta, addebito, accredito, descrizioneoperazione, saldodata, saldocontabile,
               saldodisponibile):
    try:
        fromaddr = Config.smtp_from
        username = Config.smtp_mail
        password = Config.smtp_psw
        smtpserver = smtplib.SMTP(Config.smtp_server, 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        # smtpserver.ehlo() # extra characters to permit edit
        smtpserver.login(username, password)

        header = "From: " + fromaddr + "\r\n"
        header += "To: " + ", ".join(Config.smtp_tomail) + "\r\n"
        header += "Subject: PostePay rilevato nuovo movimento \r\n"
        header += "Date: " + datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S -0000") + "\r\n\r\n"

        msg = header + "Contabile: " + datacontabile + "\n"
        msg += "Valuta: " + datavaluta + "\n"
        msg += "Addebito: " + addebito + "\n"
        msg += "Accredito: " + accredito + "\n"
        msg += "Descrizione: " + descrizioneoperazione + "\n"
        msg += "\n"
        msg += "Saldo Data: " + saldodata + "\n"
        msg += "Saldo Contabile: " + saldocontabile + "\n"
        msg += "Saldo Disponibile: " + saldodisponibile + "\n"
        msg += "\n\n"

        smtpserver.sendmail(fromaddr, Config.smtp_tomail, msg)

        smtpserver.quit()
    except Exception as e:
        logging.error(e, exc_info=True)
        pass


def load_analyzed_case():
    try:
        f = open("postepay_movimenti.txt", "r")

        for line in f:
            if line:
                line = line.rstrip()
                movimentiList.append(line)

        f.close()

    except IOError as e:
        logging.error(e, exc_info=True)
        sys.exit()
    except Exception as e:
        logging.error(e, exc_info=True)
        raise


def save_analyzed_case(casehash):
    try:
        f = open("postepay_movimenti.txt", "a")
        f.write(casehash + "\n")
        f.close()
    except IOError as e:
        logging.error(e, exc_info=True)
        sys.exit()
    except Exception as e:
        logging.error(e, exc_info=True)
        raise


def main():
    # Carico casi gia analizzati
    load_analyzed_case()

    # Apro una sessione Requests per ottenere i cookie di autenticazione
    session = requests.Session()
    url = "https://securelogin.bp.poste.it/jod-fcc/login"
    data = {"username": Config.posteusername, "password": Config.postepassword}
    session.post(url, data=data, headers=headerdesktop, timeout=timeoutconnection)
    cookie = session.cookies.get_dict()
    # Acquisisco la pagina con i movimenti della carta
    url = "https://postepay.poste.it/portalppay/viewListaMovimentiAction.do"
    data = {"cvv2": "", "dataAA": "", "dataMM": "", "numeroCarta": "", "numeroMovimenti": "40", "prosegui": "esegui",
            "selPan": Config.posteidcarta}
    page = requests.post(url, data=data, cookies=cookie, headers=headerdesktop, timeout=timeoutconnection)

    # Scrappo il contenuto della pagina per acquisire l'elenco dei movimenti
    soup = BeautifulSoup(page.text, "html.parser")

    for tablesaldo in soup.find_all("table", attrs={"class": "t-data", "brk:name": "listamov_table"}):
        for idx, row in enumerate(tablesaldo.findAll("tr")):

            # Se sto analizzando la prima riga della tabella (ovvero quella con i titoli) salto e proseguo
            if idx == 0:
                continue

            cells = row.findAll("td")

            saldodata = cells[0].text.strip()
            saldocontabile = cells[1].text.strip()
            saldocontabile = saldocontabile.replace("\t", "")
            saldocontabile = saldocontabile.replace(" ", "")
            saldocontabile = saldocontabile.replace("\r", "")
            saldocontabile = saldocontabile.replace("\n", "")

            saldodisponibile = cells[2].text.strip().replace("\t", "")
            saldodisponibile = saldodisponibile.replace("\t", "")
            saldodisponibile = saldodisponibile.replace(" ", "")
            saldodisponibile = saldodisponibile.replace("\r", "")
            saldodisponibile = saldodisponibile.replace("\n", "")

    for table in soup.find_all("table", attrs={"class": "t-data", "id": "row"}):
        for idx, row in enumerate(table.findAll("tr")):

            # Se sto analizzando la prima riga della tabella (ovvero quella con i titoli) salto e proseguo
            if idx == 0:
                continue

            cells = row.findAll("td")

            datacontabile = cells[0].text.strip()
            datavaluta = cells[1].text.strip()
            addebito = cells[2].text.strip()
            accredito = cells[3].text.strip()
            descrizioneoperazione = cells[4].text.strip()

            # Calcolo HASH della descrizione e della data valuta per identificare univocamente ogni movimento
            hashare = datavaluta + descrizioneoperazione
            casehash = hashlib.sha256(hashare.encode()).hexdigest()

            if casehash not in movimentiList:
                logging.info("Nuovo movimento rilevato", exc_info=True)

                # Invio una eMail di notifica
                send_email(datacontabile, datavaluta, addebito, accredito, descrizioneoperazione, saldodata,
                           saldocontabile, saldodisponibile)

                # Salvo il nuovo movimento
                movimentiList.append(casehash)
                save_analyzed_case(casehash)


if __name__ == "__main__":
    main()
