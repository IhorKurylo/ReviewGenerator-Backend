from fastapi import APIRouter, Request, FastAPI, requests

from app.Utils.Get_email_content import get_access_token, get_account_id, get_mail_context, get_mail_list



router = APIRouter()



@router.route('/callback/', methods=['GET', 'POST'])
def zoho_callback_route(request: Request):
    print("here")
    code = request.query_params.get('code', None)
    print(code)
    if code is not None:
        get_access_token(request, code)
        get_account_id()
    for i in range(0, 80):
        print("step: ", i)
        if get_mail_list(1 + i*200) == False :
            break
    # get_mail_list()
    return []


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



