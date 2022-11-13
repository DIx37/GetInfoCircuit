<p>Скрипт для сбора информации о подключении с возможность её отправки на почту</p>
<p>Для отправки почты настройте в NetBox "/opt/netbox/netbox/netbox/configuration.py":</p>
<pre><code class="language-python"># Email settings
EMAIL = {
	'SERVER': 'smtp.server.site',
	'PORT': 587,
	'USERNAME': 'email',
	'PASSWORD': 'pass',
	'USE_SSL': False,
	'USE_TLS': True,
	'TIMEOUT': 10,  # seconds
	'FROM_EMAIL': 'email',
}</code></pre>