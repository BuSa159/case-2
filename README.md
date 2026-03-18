# case-2
vergelijken van aandelen. 

Case 2 aandelen 
1.	Wat willen we: 
Een streamlit app, waarbij we meerdere grafieken, pie-charts maken voor diverse olie bedrijven 
Olie-bedrijven: 

Rang	Bedrijf	Beurs (Land)	Ticker	Marktwaarde (Schatting)
1	ExxonMobil	NYSE (VS)	XOM	            ~$617 mld
2	Chevron	NYSE (VS)	CVX                	~$372 mld
3	Shell	Euronext / LSE (NL/VK)	SHEL	  ~$240 mld
4	TotalEnergies	Euronext (FR)	TTE	      ~$192 mld
5	ConocoPhillips	NYSE (VS)	COP	        ~$140 mld
6	BP	LSE (VK)	BP	                    ~$108 mld
7	Enbridge	NYSE / TSX (CA/VS)	ENB	    ~$117 mld
8	Equinor	Oslo / NYSE (NO)	EQNR	      ~$107 mld
9	Southern Company	NYSE (VS)	SO	      ~$96 mld
10	Eni	Milan / NYSE (IT)	E	            ~$88 mld




API codes: 

Welcome to Alpha Vantage! 
Here is your API key: 046SOW0RCBGPECLG. 

Finnhub.io 
API: d6okk81r01qnu98if63gd6okk81r01qnu98if640 


Ideeën: 
Data verzameling: 
  1. twee API's gebruikt om data te joinen.

Data verkenning: 
1. data verkennen en kwaliteit verbeteren waar nodig

Analyse: 
1. analyse toot vergaand begrip van data science. beschrijvende analyse, statistiek/voorspellend.
2. nieuwe variabelen: Koers/Winst verhouding, daar tegenover met wat is de business return (100/P/E verhoduing)

Slider: 
1. 

checkbox 
1. meerdere aandelen, om elkaar te vergelijken. wat we kunnen doen is de verschillende waarderings methoden met elkaar koppelen.

Dropdown menu
1. ondersteunt meerdere keuzes tegelijk.








Uitleg over het model: 

Deze tabel is een klassiek waarderingsmodel (een Discounted Earnings model). Het doel is simpel: uitrekenen wat een aandeel vandaag waard is, gebaseerd op hoeveel winst het bedrijf de komende 10 jaar gaat maken.

Hier is de uitleg in begrijpelijke taal:

1. De Basis: Wat verwachten we?
In alle drie de scenario's gaat het model uit van een winst (Earnings per share) van $5,00 per jaar. Er is voor de simpelheid gekozen voor 0% groei. Het model kijkt naar de periode van 2026 tot 2035.

2. De "Discount Rate" (De 10% PV)
Dit is het belangrijkste concept. Geld dat je pas over 10 jaar krijgt, is vandaag minder waard dan geld dat je nú krijgt.

Het model gebruikt een Discount Rate van 10%.

Je ziet dat die winst van $5,00 in 2026 vandaag nog $0,23 waard is in de berekening (volgens de factor in de tabel), en dit wordt elk jaar minder.

Opmerking: In deze tabel lijkt de PV-berekening specifiek toegepast op het dividendgedeelte of een fractie, aangezien $5,00 met 10% korting na één jaar normaal $4,54 zou zijn. Hier is een factor gebruikt.

3. De Drie Scenario's (De "Wat als?" vragen)
Het verschil tussen de scenario's zit hem in de Terminal Multiple. Dit is de prijs die iemand in het jaar 2035 zou willen betalen voor het aandeel (vergelijkbaar met een K/W-verhouding).

Scenario 1 (Base Case - Normaal): Men betaalt 15x de winst in 2035. De "eerlijke waarde" nu is $30,45.

Scenario 2 (Best Case - Optimistisch): De markt is blij en betaalt 20x de winst. De waarde nu is $40,09.

Scenario 3 (Worst Case - Pessimistisch): De markt is somber en betaalt slechts 10x de winst. De waarde nu is $20,81.

4. De Conclusie: Wat is het aandeel waard?
Onderaan zie je de Gewogen Gemiddelde Berekening. Omdat we niet weten welk scenario uitkomt, geven we ze allemaal een kans:

Scenario 1 (34% kans)

Scenario 2 (33% kans)

Scenario 3 (33% kans)

Als je deze kansen bij elkaar optelt, kom je uit op een intrinsieke waarde van $30,45.

Wat betekent dit voor jou als belegger?
Is de huidige beurskoers lager dan $30,45? Dan is het aandeel volgens dit model "goedkoop" (ondergewaardeerd).

Is de koers hoger dan $30,45? Dan is het aandeel "duur" (overgewaardeerd).

Samengevat: Dit model zegt dat als dit bedrijf de komende 10 jaar stabiel $5 winst per aandeel blijft maken, het aandeel vandaag ongeveer drie tientjes waard is.

Zal ik eens voor je kijken wat er gebeurt met de waarde als we uitgaan van een kleine groei (bijv. 5%) in plaats van 0%? Dat verandert het plaatje namelijk enorm!

