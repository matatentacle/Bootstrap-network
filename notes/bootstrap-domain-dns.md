# bootstrapcharity.com domain, DNS, web and mail (public records, 20 Oct 2026)

Who manages it is NOT recorded anywhere in this workspace or in Mat's email. Everything
below is from RDAP, DNS and HTTP lookups on 20 Oct 2026.

## Registrar
- GoDaddy.com, LLC (IANA 146). Registrant and technical contact masked by Domains By Proxy.
- Registered 22 Nov 2018, expires 22 Nov 2028, last changed 24 Nov 2025.
- All client locks on (delete/renew/transfer/update prohibited). Not DNSSEC signed.
- Someone holds a GoDaddy login for it. Unknown who.

## DNS hosting
- Registry nameservers: ns1/ns2.twoshoeshosting.com. These resolve to the same IPs as
  ns1/ns2.siteground.net, i.e. a white-labelled SiteGround reseller ("Two Shoes Hosting").
- Live SOA says ns1.siteground.net / admins.siteground.com.
- So the zone lives in a SiteGround account, almost certainly reached via Two Shoes Hosting,
  which looks like a small web agency / reseller. Likely the people who built the website.

## Website
- A record 185.199.220.98, rDNS c98.lon.cloudhosting.net, block UK-KRYSTAL (Krystal Hosting
  Ltd, London). LiteSpeed server.
- WordPress 7.1.3 with Elementor 4.3.4.
- Note the web host (Krystal) is different from the DNS host (SiteGround). Two accounts.

## Email
- Google Workspace: MX aspmx.l.google.com and alts; SPF v=spf1 include:_spf.google.com ~all.
- Two google-site-verification TXT records.
- DMARC: v=DMARC1; p=none; rua=mailto:dmarc@bootstrap.com
  That rua address is on bootstrap.com, not bootstrapcharity.com. Almost certainly a typo, so
  DMARC reports go to a stranger or nowhere. Worth fixing when someone has DNS access.

## Open question
- Ask David or Ryan who holds the GoDaddy login and the Two Shoes / SiteGround account.
  Ryan (Communications) is the likely website owner.
