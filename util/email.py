"email vendor wrapper"

import os, requests

DOMAIN = 'https://api.postmarkapp.com/email'

def send_email(to_, subject, html_body, from_='"Small gatherings" <welcome@smallgatherings.app>'):
  # todo: make this a queue
  # todo: trace or time the write here
  # todo: must rate limit globally & per normalized destination email and per source IP
  res = requests.post(
    DOMAIN,
    headers={"X-Postmark-Server-Token": os.environ['POSTMARK_PASS']},
    json={
      'From': from_,
      'To': to_,
      'Subject': subject,
      'HtmlBody': html_body,
    }
  )
  res.raise_for_status()
  return res
