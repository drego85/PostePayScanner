#!/usr/bin/python3
import sys
import json
import Config
import hashlib
import smtplib
import logging
import requests
from random import randint
from datetime import datetime
from bs4 import BeautifulSoup

# Inizializzo i LOG
logging.basicConfig(filename="postepay.log",
                    format="%(asctime)s - %(funcName)10s():%(lineno)s - %(levelname)s - %(message)s",
                    level=logging.INFO)

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
    # Carico transazioni gia analizzate
    load_analyzed_case()

    # Apro una sessione requests per autenticarmi e ottenere i cookie di sessione
    url = "https://securelogin.bp.poste.it/jod-fcc/login"

    headerdesktop = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:62.0) Gecko/20100101 Firefox/62.0",
                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                     "Accept-Language": "it,en-US;q=0.7,en;q=0.3",
                     "Accept-Encoding": "gzip, deflate, br",
                     "Referer": "https://www.poste.it/index.html",
                     "Content-Type": "application/x-www-form-urlencoded",
                     "Content-Length": "170",
                     "DNT": "1",
                     "Connection": "keep-alive",
                     "Upgrade-Insecure-Requests": "1",
                     "Pragma": "no-cache",
                     "Cache-Control": "no-cache"}

    session = requests.Session()
    data = {"username": Config.posteusername, "password": Config.postepassword}
    session.post(url, data=data, headers=headerdesktop, timeout=timeoutconnection)
    cookie = session.cookies.get_dict()

    # Acquisisco i movimenti della carta
    url = "https://postepay.poste.it/ppay/private/rest/ppayUtenteService/dettaglioMovimenti"

    data = {"data": {"alias": Config.posteidcarta, "numeroMovimentiPagina": "40", "numeroMovimentiSaltoPaginazione": 0}}

    headerdesktop = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:62.0) Gecko/20100101 Firefox/62.0",
                     "Accept": "application/json, text/plain, */*",
                     "Accept-Language": "it,en-US;q=0.7,en;q=0.3",
                     "Accept-Encoding": "gzip, deflate, br",
                     "Referer": "https://postepay.poste.it/ppay/private/pages/index.html",
                     "requestID": "PPAY.WEB.%s" % randint(1000000000000, 9999999999999),
                     "requestTimestamp": datetime.utcnow().strftime("%d/%m/%Y - %H:%M:%S"),
                     "Content-Type": "application/json;charset=utf-8",
                     "Content-Length": "194",
                     "DNT": "1",
                     "Connection": "keep-alive",
                     "Pragma": "no-cache",
                     "Cache-Control": "no-cache"}

    page = requests.post(url, json=data, cookies=cookie, headers=headerdesktop, timeout=timeoutconnection)

    data = json.loads(page.text)

    if data:
        # Identificico il saldo attuale della carta
        saldodata = datetime.utcfromtimestamp(data["data"]["datiSaldo"]["dataSaldo"] / 1000).strftime("%d/%m/%Y")
        saldocontabile = str(data["data"]["datiSaldo"]["saldoContabile"])
        saldocontabile = "%s,%s" % (saldocontabile[:-2], saldocontabile[-2:])
        saldodisponibile = str(data["data"]["datiSaldo"]["saldoDisponibile"])
        saldodisponibile = "%s,%s" % (saldodisponibile[:-2], saldodisponibile[-2:])

        # Identifico ogni singolo movimento
        for each in data["data"]["listaMovimenti"]:
            importo = str(each["importo"])
            accredito = ""
            addebito = ""

            if "POSITIVO" in each["segno"]:
                accredito = "+%s,%s" % (importo[:-2], importo[-2:])
            else:
                addebito = "-%s,%s" % (importo[:-2], importo[-2:])

            descrizioneoperazione = each["descrizione"]
            datacontabile = datetime.utcfromtimestamp(each["dataContabile"] / 1000).strftime("%d/%m/%Y")
            datavaluta = datetime.utcfromtimestamp(each["dataValuta"] / 1000).strftime("%d/%m/%Y")

            # Calcolo HASH della descrizione e della data valuta per identificare univocamente ogni movimento
            transaction = datavaluta + descrizioneoperazione
            hashtransaction = hashlib.sha256(transaction.encode()).hexdigest()

            if hashtransaction not in movimentiList:
                logging.info("Nuovo movimento rilevato")

                # Invio una eMail di notifica
                send_email(datacontabile, datavaluta, addebito, accredito, descrizioneoperazione, saldodata,
                           saldocontabile, saldodisponibile)

                # Salvo il nuovo movimento
                movimentiList.append(hashtransaction)
                save_analyzed_case(hashtransaction)


if __name__ == "__main__":
    main()
