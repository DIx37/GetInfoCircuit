#!/usr/bin/python3
# Dmitrii Karnov <dkarnov@gmail.com>


from circuits.models import Provider, Circuit, CircuitType, CircuitTermination
from tenancy.models import ContactAssignment
from email.mime.text import MIMEText
from dcim.models import Site
from extras.scripts import *
import netbox.configuration
import smtplib


class GetProviderInfo(Script):
	class Meta:
		name = "GetProviderInfo"
		description = "Поиск информации по провайдеру"
		commit_default = False
		job_timeout = 120


	site = ObjectVar(
		model = Site,
		description = "Выберите Объект"
	)


	circuit_type = ObjectVar(
		model = CircuitType,
		description = "Выберите тип подключения",
		query_params = {
			'circuits': '$circuit'
		}
	)


	check_send_email = BooleanVar(
		description = "Отправить на почту?"
	)


	def run(self, data, commit):
		try:
			log_info = ""
			site = data['site']
			circuit_type = data['circuit_type']
			name = site.name
			physical_address = site.physical_address
			latitude = site.latitude
			longitude = site.longitude
			site_comments = site.comments
			circuit_type_name = circuit_type.name


			log_info += f"{name}<p>"
			log_info += f"<b>Адрес:</b> {physical_address}<p>"
			if latitude != None and longitude != None:
				log_info  += f"<b>Широта:</b> {latitude} <b>Долгота:</b> {longitude}<p>"
			if site_comments != "":
				log_info += f"<b>Комментарий Объекта:</b> {site_comments}<p>"
			log_info += f"<b>Тип подключения:</b> {circuit_type_name}<p>"


			for i in CircuitTermination.objects.filter(site_id=site.id):
				for j in Circuit.objects.filter(id=i.circuit.id):
					if circuit_type.id == j.id:
						provider_id = j.provider.id


			provider_name = Provider.objects.get(id = provider_id).name
			provider_account = Provider.objects.get(id = provider_id).account
			provider_portal_url = Provider.objects.get(id = provider_id).portal_url
			provider_comments = Provider.objects.get(id = provider_id).comments


			log_info += f"<b>Провайдер:</b> {provider_name}<p>"
			log_info += f"<b>Договор:</b> {provider_account}<p>"
			if provider_portal_url != None:
				log_info += f"<b>Сайт:</b> {provider_portal_url}<p>"
			if provider_comments != None:
				log_info += f"<b>Комментарий Провайдера:</b> {provider_comments}<p>"


			contact_list = ""
			for contact in ContactAssignment.objects.filter(object_id = provider_id):
				contact_list += f'''
					<ul>
						<li class="null"><em><strong>{contact.contact.name}</strong></em><br>
							<ul>
								<li class="null"><strong>Телефон:</strong> <a href="tel:{contact.contact.phone}">{contact.contact.phone}</a></li>
								<li class="null"><strong>Почта:</strong> {contact.contact.email}</li>
							</ul>
						</li>
					</ul>'''
				log_info += f"&nbsp;&nbsp;&nbsp;<b>Имя:</b> {contact.contact.name}<p>&nbsp;&nbsp;&nbsp;<b>Телефон:</b> {contact.contact.phone}<p>&nbsp;&nbsp;&nbsp;<b>Почта:</b> {contact.contact.email}<p>"


			circuit_id = Circuit.objects.get(provider_id = provider_id).id
			circuit_termination_date = Circuit.objects.get(provider_id = provider_id).termination_date
			circuit_description = Circuit.objects.get(provider_id = provider_id).description
			circuit_a_port_speed = Circuit.objects.get(provider_id = provider_id).termination_a.port_speed
			circuit_z_port_speed = Circuit.objects.get(provider_id = provider_id).termination_z.port_speed
			circuit_a_upstream_speed = Circuit.objects.get(provider_id = provider_id).termination_a.upstream_speed
			circuit_z_upstream_speed = Circuit.objects.get(provider_id = provider_id).termination_z.upstream_speed
			circuit_comments = Circuit.objects.get(provider_id = provider_id).comments


			if circuit_id != None:
				log_info += f"<b>Договор подключения:</b> {circuit_id}<p>"
			if circuit_termination_date != None:
				log_info += f"<b>Дата подключения:</b> {circuit_termination_date}<p>"
			if circuit_description != None:
				log_info += f"<b>Описание:</b> {circuit_description}<p>"
			if circuit_z_port_speed != None and circuit_z_upstream_speed != None:
				log_info += f"<b>Скорость:</b> D {circuit_z_port_speed / 1000} Mbps / U {circuit_z_upstream_speed / 1000} Mbps<p>"
			if circuit_a_port_speed != None and circuit_a_upstream_speed != None:
				log_info += f"<b>Скорость A:</b> D {circuit_z_port_speed / 1000} Mbps / U {circuit_z_upstream_speed / 1000} Mbps<p>"
			if circuit_comments != "":
				log_info += f"<b>Комментарий Подключения:</b> {circuit_comments}<p>"
			self.log_info(log_info)


			if data['check_send_email'] == True:
				if "@" in self.request.user.email:
					send_email(self.request.user.email,
								name,
								physical_address,
								latitude,
								longitude,
								site_comments,
								circuit_type_name,
								contact_list,
								provider_name,
								provider_account,
								provider_portal_url,
								provider_comments,
								circuit_id,
								circuit_termination_date,
								circuit_description,
								circuit_a_port_speed,
								circuit_z_port_speed,
								circuit_a_upstream_speed,
								circuit_z_upstream_speed,
								circuit_comments
								)
					self.log_info(f"Письмо отправлено на {self.request.user.email}")
				else:
					self.log_failure("Почта не найдена, добавьте Вашу почту в профиль.")


			self.log_success("Скрипт успешно завершён")
		except Exception as err:
			self.log_failure(f"Произошла ошибка:\n{err}")


def send_email(email_to,
				name,
				physical_address,
				latitude,
				longitude,
				site_comments,
				circuit_type_name,
				contact_list,
				provider_name,
				provider_account,
				provider_portal_url,
				provider_comments,
				circuit_id,
				circuit_termination_date,
				circuit_description,
				circuit_a_port_speed,
				circuit_z_port_speed,
				circuit_a_upstream_speed,
				circuit_z_upstream_speed,
				circuit_comments
				):


	server = smtplib.SMTP(netbox.configuration.EMAIL['SERVER'], netbox.configuration.EMAIL['PORT'])
	if netbox.configuration.EMAIL['USE_TLS'] == True:
		server.starttls()
	else:
		server.starttls()


	body = f"<h2>{name}</h2>"
	body += f"<p><strong>Адрес:</strong> {physical_address}</p>"
	body += f"<p><strong>Тип подключения:</strong> {circuit_type_name}</p>"
	body += f"<p><strong>Провайдер:</strong> {provider_name}</p>"
	if circuit_termination_date != None:
		body += f"<p><strong>Дата подключения:</strong> {circuit_termination_date}</p>"
	if site_comments != "":
		body += f"<p><strong>Комментарий Места: </strong>{site_comments}</p>"
	if provider_comments != "":
		body += f"<p><strong>Комментарий Провайдера: </strong>{provider_comments}</p>"
	if circuit_comments != "":
		body += f"<p><strong>Комментарий Подключения: </strong>{circuit_comments}</p>"
	if circuit_description != "":
		body += f"<p><strong>Описание Подключения: </strong>{circuit_description}</p>"
	body += f"<p><strong>Договор: </strong>{provider_account}&nbsp; /&nbsp; {circuit_id}</p>"
	if provider_portal_url != "":
		body += f'<p><strong>Ссылка:</strong> <a href="{provider_portal_url}">{provider_portal_url}</a></p>'
	if circuit_z_port_speed != None and circuit_z_upstream_speed != None:
		body += f"<p><strong>Скорость:</strong> D {circuit_z_port_speed / 1000} Mbps / U {circuit_z_upstream_speed / 1000} Mbps</p>"
	if circuit_a_port_speed != None and circuit_a_upstream_speed != None:
		body += f"<p><strong>Скорость A:</strong> D {circuit_a_port_speed / 1000} Mbps / U {circuit_a_upstream_speed / 1000} Mbps</p>"
	body += f"<p><strong>Контакты:</strong></p>"
	body += contact_list


	html = f"""
	<!DOCTYPE html>
	<html lang="ru">
		<head>
			<meta charset="UTF-8">
			<meta http-equiv="X-UA-Compatible" content="IE=edge">
			<meta name="viewport" content="width=device-width, initial-scale=1.0">
			<title>Document</title>
		</head>
		<body>
            {body}
		</body>
	</html>
	"""


	try:
		server.login(netbox.configuration.EMAIL['USERNAME'], netbox.configuration.EMAIL['PASSWORD'])
		msg = MIMEText(html, "html")
		msg["From"] = netbox.configuration.EMAIL['USERNAME']
		msg["To"] = email_to
		msg["Subject"] = f"Информация по подключению {name}"
		server.sendmail(netbox.configuration.EMAIL['USERNAME'], email_to, msg.as_string())
	except Exception as err:
		return err