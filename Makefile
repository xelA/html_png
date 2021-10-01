target:
	@echo Welcome to Chrome_HTML Makefile. Use help if you need information.

help: ## Shows this message as we speak
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

start: ## Create a PM2 instance of the website and start it
	pm2 start pm2.json

clean: ## Kills the process (Linux only)
	sudo pkill -9 chrome
	pm2 delete pm2.json

clean_update: ## Kills the process, pulls from GitHub and runs again (Linux only)
	sudo pkill -9 chrome
	pm2 delete pm2.json
	git pull
	pm2 start pm2.json
