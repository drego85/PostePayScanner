# PostePay Scanner

Scanner in grado di notificare, tramite eMail, nuovi movimenti sull'estratto conto della PostePay di Poste Italiane.

La notifica via eMail conterrà le seguenti informazioni:
* Data di valuta;
* Data contabile;
* Addebito o Accredito;
* Descrizione movimento;
* Saldo Contabile e Disponibile.

**Esempio Notifica eMail**

![Esempio Notifica](https://raw.githubusercontent.com/drego85/PostePayScanner/master/screenshots/notifica_email.png)

#### Configurazione

Il file Config.sample.py va rinominato in Config.py e compilato con i seguenti dati:
* smtp_mail > eMail di autenticazione al server SMTP
* smtp_psw > password di autenticazione al server SMTP
* smtp_server > indirizzo del server SMTP
* smtp_tomail > Destinatari eMail di notifica
* smtp_from > Mittente dell'eMail di notifica 
* posteusername > Username di accesso al portale di Poste Italiane
* postepassword > Password di accesso al portale di Poste Italiane
* posteidcarta > Carta ID (non è il numero/pan della vostra carta di credito) di seguito un approfondimento

####Carta ID

Visualizzando la pagina di ["Saldo e Lista Movimenti"](https://postepay.poste.it/portalppay/startListaMovimentiAction.do) analizzando il codice HTML della pagina è possibile identificare il Card ID associato alla vostra carta pregapata. Inserire pertanto tale valore, comprensivo degli zero iniziali, nel file di configurare.

![Esempio codice HTML](https://raw.githubusercontent.com/drego85/PostePayScanner/master/screenshots/cartaid.png)

