import imaplib
import email
from email.header import decode_header
import datetime
import pytz
from pathlib import Path

def get_mail(username, password, sender_name, t_start=datetime.datetime.now()):#datetime.datetime.fromisoformat('2021-02-15T11:41:57')
    
    all_mails = []
    ##username = "gautam.luvg@gmail.com"
    ##password = "aloo4uonly"

    imap = imaplib.IMAP4_SSL("imap.gmail.com")

    try:
        imap.login(username, password)
        log = 'success'
    except imaplib.IMAP4.error:
        log = 'Unable to login. Please check Username\Password and try again.'
        return [], log
    
    status, messages = imap.select("INBOX")

    messages = int(messages[0])
    #print(messages)
    for message in range(messages, 0, -1):
        attachment = []
        break_outer_loop = False
        res, msg = imap.fetch(str(message), "(RFC822)")

        for response in msg:
            if isinstance(response, tuple):
                mail = email.message_from_bytes(response[1])

                date, encoding = decode_header(mail.get("Date"))[0]
                if isinstance(date, bytes):
                    date = date.decode(encoding)
                try:
                    date = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
                except:
                    date = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')
                date = date.astimezone(pytz.timezone('Asia/Kolkata'))
                date = date.replace(tzinfo=None)
                if date < t_start:
                    break_outer_loop = True
                    break
                
                date_str = date.strftime('%d-%b-%Y %I:%M %p')

                subject, encoding = decode_header(mail["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding)

                from_, encoding = decode_header(mail.get("From"))[0]
                if isinstance(from_, bytes):
                    from_ = from_.decode(encoding)

                
                if mail.is_multipart():
                    for part in mail.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                body = part.get_payload(decode=True).decode()
                        except:
                            pass

                        if "attachment" in content_disposition:
                            filename, encoding = decode_header(part.get_filename())[0]
                            #filename = part.get_filename()
                            if encoding is not None:
                                filename = filename.decode(encoding)
                            if filename:
                                p = Path(f'{sender_name}/mails')
                                if p.is_dir() is False:
                                    p.mkdir(parents=True, exist_ok=True)
                                filepath = p.joinpath(f'{filename}')
                                open(filepath, "wb").write(part.get_payload(decode=True))
                                attachment.append(filepath.resolve())
                else:
                    content_type = mail.get_content_type()
                    
                    if content_type == "text/plain":
                        body = mail.get_payload(decode=True).decode()

        if break_outer_loop:
            break
        all_mails.append((subject, from_, date, date_str, body, attachment))

    imap.close()
    imap.logout()

    return all_mails, log#subject, from_, date, date_str, body, attachment_flag

if __name__ == '__main__':
    username = "gautam.luvg@gmail.com"
    password = "aloo4uonly"
    sender_name = 'Luv'
    a, b = get_mail(username, password, sender_name)
    print(b)
##    for mail in a:
##        for part in mail:
##            print(part)
##        print()


##date, encoding = decode_header(m.get("Date"))[0]
##'Mon, 07 Dec 2020 23:53:23 -0800'
##
##import datetime
##d = datetime.datetime.strptime('Mon, 07 Dec 2020 23:53:23 -0800', '%a, %d %b %Y %H:%M:%S %z')
##datetime.datetime(2020, 12, 7, 23, 53, 23, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=57600)))
##
##new = d.astimezone(pytz.timezone('Asia/Kolkata'))
##datetime.datetime(2020, 12, 8, 13, 23, 23, tzinfo=<DstTzInfo 'Asia/Kolkata' IST+5:30:00 STD>)
##
##new.strftime('%I:%M %p')
##'01:23 PM'
