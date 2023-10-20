from fastapi import APIRouter, Request, Form, Response

from app.Utils.Get_email_content import get_access_token, get_account_id, get_mail_context, get_mail_list, get_mail_folders, start
from app.Utils.Pinecone import get_context


router = APIRouter()

EmailCount = 5


@router.route('/callback/', methods=['GET', 'POST'])
def zoho_callback_route(request: Request):
    print("here")
    code = request.query_params.get('code', None)
    print(code)
    if code is not None:
        get_access_token(request, code)
        get_account_id()
    get_mail_folders()
    unit = min(EmailCount, 200)
    n = int((EmailCount-1) / unit + 1)
    print(n, " ", unit)
    for i in range(0, n):
        print("step: ", i)
        if get_mail_list(565 + i * unit, unit) == False:
            break
    print("done")
    return Response(content="200", media_type="text/plain")


# @router.route('/sendmail/', methods=['GET', 'POST'])
# def send_mail_route():
#     # Send a HTML email!
#     print("sent")
#     data = ['1', '2', '3']
#     mail = render_template('mail_template.j2', data=data)
#     send_mail(mail, TO_EMAIL_ADDR)
#     return 'OK', 200


# @router.route('/getmail/', methods=['GET', 'POST'])
# def get_mail_route():
#     # Get all folders!
#     print("get")
#     get_mail_list()
#     return 'OK', 200

@router.post('/generate-response')
def generate_response_route(email: str = Form(...), keywords: str = Form(...)):
    return get_context(email, keywords)


@router.post('/extract-email-content')
def extract_email_content(clientId: str = Form(...), clientSecret: str = Form(...), emailCount: int = Form(...)):
    # print(clientId, clientSecret)
    global EmailCount
    EmailCount = emailCount
    return start(clientId, clientSecret)
