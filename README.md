# Ficbook Parser

This project in not completely operational since it lacks some of its backend components, bearable UI, and correct Docker configuration.

Additionally, it does not have a LICENCE which is **intentional**. Hence copying and using the code base is strictly *discouraged*. 

docker command  
`docker build -t ficbook-parser . && docker stop ficbook-parser && docker rm ficbook-parser && docker run -d -p 5555:80 --name ficbook-parser -v $PWD:/app ficbook-parser`