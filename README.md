# HNS Pay

HNS Pay is a simple payment gateway for Handshake domains. It allows you to accept payments in HNS for your products and services.

## Deploying HNS Pay

The easiest way to deploy HNS Pay is to use docker.  

```bash
docker volume create hns-pay
docker run -d -p 5000:5000 -v hns-pay:/app/data --name hns-pay \
 -e HSD_IP=localhost -e HSD_API_KEY=yourhsdapikey -e WALLET=primary -e GLOBAL_WEBHOOK=webhook_for_all_users \ 
 git.woodburn.au/nathanwoodburn/hns-pay:latest
```

If you have a encrypted wallet you can also pass the `WALLET_PASS` environment variable.