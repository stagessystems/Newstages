# -*- coding: utf-8 -*-
from odoo import http
import json
from odoo.http import request
import logging
import requests
from datetime import datetime
_logger = logging.getLogger(__name__)


class RestApi(http.Controller):
    @http.route('/rest_api/rest_api/', auth='public')
    def index(self, **kw):
        x = requests.get("http://157.230.6.121:8069/api_mig/api_mig/")
        res = x.text
        json_data = json.loads(str(res))
        _logger.info("============================json_data============================")

        _logger.info(len(json_data['response']))
        # for record in json_data['response']:
        #     # _logger.info("************************"+str(record))
        #     m = request.env["hms.patient"].sudo().create(record)
        for rec in json_data['response']:
            p = request.env['hms.patient'].sudo().search([("comment","=",rec['comment'])])
            # if p:
                # if rec.get('birthday') != False:
                #     p.birthday = datetime.strptime(rec['birthday'],'%Y-%m-%d')
                #     _logger.info("=======birthday=="+str(p.birthday))
            if not p:
                _logger.info("=======rec=="+str(rec))
                m = request.env["hms.patient"].sudo().create(rec)
                
        # m = request.env["hms.patient"].sudo().create(json_data)
        return "Hello, world"
    @http.route('/rest_api/docs/', auth='public')
    def index(self, **kw):
        x = requests.get("http://157.230.6.121:8069/api_mig/docs/")
        res = x.text
        json_data = json.loads(str(res))
        _logger.info("============================json_data============================")

        _logger.info(len(json_data['response']))
        for rec in json_data['response']:
            d = request.env['hms.physician'].sudo().search([("email","=",rec['email'])])
            # if p:
                # if rec.get('birthday') != False:
                #     p.birthday = datetime.strptime(rec['birthday'],'%Y-%m-%d')
                #     _logger.info("=======birthday=="+str(p.birthday))
            if not d:
                _logger.info("=======rec=="+str(rec))
                d["specialty_id"] = 3
                m = request.env["hms.physician"].sudo().create(rec)
                
        # m = request.env["hms.patient"].sudo().create(json_data)
        return "Hello, world"
    @http.route('/rest_api/app/',  auth='public')
    def get_appointments(self, **kw):
        x = requests.get("http://157.230.6.121:8069/api_mig/appointments/")
        res = x.text
        json_data = json.loads(str(res))
        _logger.info("============================json_data============================")
        for rec in json_data['response']:
            p=request.env['hms.patient'].sudo().search([('code','=',rec['patient_id'])])
            d=request.env['hr.department'].sudo().search([('name','=',rec['department_id'])])
            ph=request.env['hms.physician'].sudo().search([('code','=',rec['physician_id'])])

            _logger.info("==========="+str(p))
            _logger.info("==========="+str(d))
            if p:
                rec['patient_id'] = p[0].id or ''
            if not p:
                continue
            if d:
                rec['department_id'] = d[0].id or ''
            if not d:
                rec.pop("department_id")
            if ph:
                rec['physician_id'] = ph[0].id 
                rec.pop("physician_name")
                rec.pop("physician_email")
                rec.pop("physician_code")

            if not ph:
                ph=request.env['hms.physician'].sudo().search([('email','=',rec['physician_email'])])
                if ph:
                    rec['physician_id'] = ph[0].id 
                    rec.pop("physician_name")
                    rec.pop("physician_email")
                    rec.pop("physician_code")
               
            if not ph:
                ph=request.env['hms.physician'].sudo().create({
                                                                "name":rec['physician_name'],
                                                                "code":rec['physician_code'],
                                                                "email":rec['physician_email'],
                                                                "specialty_id" : 3
                })
                rec.pop("physician_name")
                rec.pop("physician_email")
                rec.pop("physician_code")
                rec['physician_id'] = ph.id

            if rec['consultation_type'] == False :
                rec.pop("consultation_type")
            _logger.info(str(rec['date_to']))
            _logger.info(len(rec['date_to']))
            _logger.info(str(rec))
            if rec.get("date_to") == False:
                rec.pop("date_to")
            
            # rec['date'] = datetime.strptime(rec['date'],'%Y-%m-%d %H:%M:%S')
            # rec['date_to'] = datetime.strptime(rec['date_to'][0:20],'%Y-%m-%d %H:%M:%S')
            _logger.info(str(rec.get("date_to")))
            _logger.info(str(rec))
            m = request.env["hms.appointment"].sudo().create(rec)

        return str(json_data['response'])

    @http.route('/rest_api/inv/',  auth='public')
    def get_invoices(self, **kw):
        def _check_physician(rec):
            physician_id = request.env['hms.physician'].sudo().search([('email','=',rec['physician_email'])])
            if physician_id:
                rec['physician_id'] = physician_id[0].id
                rec.pop("physician_name")
                rec.pop("physician_email")
                rec.pop("physician_code")
                return rec
            # if not physician_id:
            #     physician_id = request.env['hms.physician'].sudo().search([('email','=',rec['physician_email'])])
            #     if physician_id:
            #         rec['physician_id'] = physician_id[0].id
            #         rec.pop("physician_name")
            #         rec.pop("physician_email")
            #         rec.pop("physician_code")
            #         return rec
            if not physician_id:
                rec['physician_id'] = False
                return rec
        x = requests.get("http://157.230.6.121:8069/api_mig/inv")
        res = x.text
        json_data = json.loads(str(res))
        # _logger.info("============================json_data============================"+str(json_data))
        for rec in json_data['response']:
            if rec.get("invoice_date") == False:
                continue
            patient_id = request.env['hms.patient'].sudo().search([('code','=',rec['patient_id'])])
            if patient_id:
                rec['patient_id'] = patient_id.id
                rec['partner_id'] = patient_id.partner_id.id
            else:
                continue

            # _logger.info("after = "+str(rec))
            rec = _check_physician(rec)
            if rec['physician_id'] == False:
                continue
                physician_id=request.env['hms.physician'].sudo().create({
                    "name":rec['physician_name'],
                    "code":rec['physician_code'],
                    "email":rec['physician_email'],
                    "specialty_id" : 5
                })
                rec.pop("physician_name")
                rec.pop("physician_email")
                rec.pop("physician_code")
                rec['physician_id'] = physician_id.id
            # _logger.info("after = "+str(rec))
            rec.pop("name")
            if rec.get("appointment_name") != False:
                appointment_id = request.env['hms.appointment'].sudo().search([('name','=',rec['appointment_name'])])
                if appointment_id:
                    rec["appointment_id"] = appointment_id[0].id
            rec.pop("appointment_name")
            rec["move_type"] = "out_invoice"
            rec["journal_id"] = request.env['account.journal'].sudo().search([('code','=','INV')])[0].id
            flag = False
            for r in rec["invoice_line_ids"]:
                product = request.env['product.product'].sudo().search([('description','=',str(r[2]['product_id']))])
                r[2].pop("product_name")
                if len(r[2]['tax_ids']) == 2:
                    r[2].pop("tax_ids")
                else:
                    tax = request.env['account.tax'].sudo().search([])
                    t = r[2]['tax_ids']
                    tt = []
                    for h in tax:
                        tt.append(h.id)
                    r[2]['tax_ids'] = [(6,0, tt )]  
                _logger.info(r)

                if not product:
                    flag = True
                if product:
                    r[2]['product_id'] = product[0].id
                    # _logger.info(str(r))
                    # _logger.info(str(product.name))
                    # r[2].pop("product_name")
            if flag:
                rec.pop("invoice_line_ids")
            # for h in rec["invoice_line_ids"]:
            #     if h[2].get("product_name"):
            #         flag = True
            # if flag:
            #     rec.pop("invoice_line_ids")


                
                
            inv = request.env['account.move'].sudo().create(rec)
            _logger.info("----------------------"+str(inv))

        return "str(json_data)"
    @http.route('/rest_api/inv/del',  auth='public')
    def del_invoices(self, **kw):

        inv = request.env['account.move'].sudo().search([('state','=','draft')])
        inv.unlink()
        return "inv del"
    @http.route('/rest_api/app/del',  auth='public')
    def del_appointment(self, **kw):

        app = request.env['hms.appointment'].sudo().search([('state','=','done')])
        for a in app:
            a.state = 'draft'
        
        app.sudo().unlink()
        ap= request.env['hms.appointment'].sudo().search([])
        ap.unlink()
        return "app del"
    @http.route('/rest_api/prd/', auth='public')
    def get_products(self, **kw):
        x = requests.get("http://157.230.6.121:8069/api_mig/prd")
        res = x.text
        json_data = json.loads(str(res))
        _logger.info("============================json_data============================")

        _logger.info(len(json_data['response']))
        m = request.env["product.product"].sudo().create(json_data['response'])
        return "Hello, world"
    
#     @http.route('/rest_api/rest_api/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('rest_api.listing', {
#             'root': '/rest_api/rest_api',
#             'objects': http.request.env['rest_api.rest_api'].search([]),
#         })

#     @http.route('/rest_api/rest_api/objects/<model("rest_api.rest_api"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rest_api.object', {
#             'object': obj
#         })
