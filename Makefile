target:
	@echo Welcome to Chrome_HTML Makefile. Use help if you need information.

help: ## Shows this message as we speak
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

start: ## Create a PM2 instance of the website and start it
	pm2 start pm2.json

clean: ## Remove/kill anything related to the API (Linux only)
	sudo pkill -9 chrome
	pm2 delete Chrome_HTML
