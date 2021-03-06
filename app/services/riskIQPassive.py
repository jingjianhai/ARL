from app import utils
from app.config import Config

logger = utils.get_logger()

class RiskIQPassive():
    def __init__(self, auth_email, auth_key):
        self.auth_email = auth_email
        self.auth_key = auth_key
        self.subdomain_api = "https://api.passivetotal.org/v2/enrichment/subdomains"
        self.quota_api = "https://api.passivetotal.org/v2/account/quota"

    def search_subdomain(self, target):
        params = {
            "query":"*.{}".format(target)
        }
        auth = (self.auth_email, self.auth_key)
        conn = utils.http_req(self.subdomain_api,
                              params = params,
                              auth=auth,
                              timeout=(20, 120))
        data = conn.json()

        subdomains = []
        for item in data['subdomains']:
            item = item.strip("*.")
            domain = "{}.{}".format(item, target)
            if utils.domain_parsed(domain):
                subdomains.append(domain)

        return list(set(subdomains))



    def quota(self):
        auth = (self.auth_email, self.auth_key)
        conn = utils.http_req(self.quota_api, auth=auth)
        data = conn.json()
        count = data["user"]["counts"]["search_api"]
        limit = data["user"]["limits"]["search_api"]
        return count, limit




def riskiq_search(domain):
    try:
        r = RiskIQPassive(Config.RISKIQ_EMAIL, Config.RISKIQ_KEY)
        count, limit = r.quota()
        logger.info("riskiq api quota [{}/{}] [{}]".format(count, limit, domain))
        if count < limit:
            return  r.search_subdomain(domain)
    except Exception as e:
        if "'user'" == str(e):
            logger.warning("riskiq api auth error ({}, {})".format(Config.RISKIQ_EMAIL,
                                                                  Config.RISKIQ_KEY))

        else:
            logger.exception(e)

    return  []

def riskiq_quota():
    try:
        r = RiskIQPassive(Config.RISKIQ_EMAIL, Config.RISKIQ_KEY)
        count, limit =   r.quota()
        return limit - count
    except Exception as e:
        logger.exception(e)

    return 0