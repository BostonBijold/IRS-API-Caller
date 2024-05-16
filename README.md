# IRS-API-Caller
A simple API microservice to call IRS APIs for licensed CPAs. Written using Publication-5718 and Application Program Interface (API) User Guide for Transcript Delivery System (TDS) (Available for licenced CPAs from the IRS) 

https://www.irs.gov/pub/irs-pdf/p5718.pdf

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install packages.

```bash
$ pip install beautifulsoup4
$ pip install Flask
$ python -m pip install requests
```

## Redacted Variables
Before running the program replace the place holder text for: (line, placeholder) 
19 - "<private key>"
21 - "<public key>"
23 - "<IRS Client ID>"
27 - "<kid>"
40 - "<IRS user ID>"

Refer to IRS publications for details for replacement values.

## Usage 

Run main.py locally or on a server.

Once called, the program will generate 2 JWTs that will expire in 15 minutes and request a access token with the same experation. The token is used to call the IRS for transcripts for indeviduals who have a signed and accepted power of attorney allowing access for their CPA. The transcript is parsed and a Json list of transactions is returned to the caller.   


## License

[MIT](https://choosealicense.com/licenses/mit/)
