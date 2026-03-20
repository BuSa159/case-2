#streamlit link
https://case-2-zz8zf656wmlzfsxm4mxyed.streamlit.app/

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

financial modeling prep: 
?apikey=43a39GW86qFEdUpYJ3crtC8CCpa88yrz at the end of every request.

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


Antwoord van Gemini voor de slider, checkbox en dropdown. 

Topidee. Als analist wil ik een dashboard dat niet alleen data spuwt, maar dat me dwingt om keuzes te maken. Voor een Streamlit-applicatie gericht op aandelenanalyse kunnen we deze interactieve elementen heel slim inrichten.Hier is een conceptueel ontwerp voor je Streamlit-pagina:

1. De "Interdependent" Sector SliderIn plaats van twee losse sliders, maken we een Capital Allocation Slider. Deze dwingt de gebruiker te kiezen tussen Dividend en R&D (Groei).Hoe het werkt: Als je de slider naar "Dividend" schuift, neemt het budget voor "R&D" automatisch af (som = 100%).Visualisatie: Gebruik een gestapelde staafgrafiek (st.bar_chart) die direct van kleur verandert.Groen: Veel dividend (veilig, inkomen).Blauw: Veel R&D (risicovol, groei).Code-logica:Pythondiv_weight = st.slider("Kapitaalverdeling (Dividend vs Groei)", 0, 100, 50)
growth_weight = 100 - div_weight
st.write(f"Sectorkarakter: {div_weight}% Value / {growth_weight}% Growth")

2. De "Smart Auditor" CheckboxesDit is essentieel voor risicoanalyse. We maken een sectie voor Investment Constraints.Het Conflict: Je kunt niet tegelijkertijd "Hoog Dividend" en "Snelle Tech Groei" aanvinken zonder een waarschuwing te krijgen (omdat die zelden samengaan).Feedback: Gebruik st.warning of st.error als er een onlogische combinatie wordt gekozen.Opzet:Hoofd-checkbox: "Filter op ESG-criteria"Sub-checkboxes: "Geen fossiele brandstoffen", "Groene energie focus".Conflict-detectie: Als de gebruiker "Geen fossiele brandstoffen" selecteert én in het dropdown-menu "ExxonMobil" kiest, verschijnt er een melding: "Let op: ExxonMobil voldoet niet aan uw ESG-filter."

3. De Multi-Select Quick ViewVoor het vergelijken van aandelen is de st.multiselect perfect, maar we voegen een "Metrics-sneltreinstrip" toe.Functionaliteit: Zodra je tickers selecteert (bijv. AAPL, MSFT, XOM), verschijnen er direct kleine "Metric Cards" (st.metric) naast elkaar.Snelheid: Gebruik st.columns om de data van de geselecteerde aandelen direct onder de dropdown te tonen, zodat je niet hoeft te scrollen.UI/UX Structuur (Concept)ComponentFunctieGebruikerservaringMultiselectst.multiselect(['XOM', 'CVX', 'BP'])Selecteer je watchlist; verschijnt direct in de grafiek.Logic Checkboxesst.checkbox('Deep Value Strategy')Activeert filters; geeft rood licht bij conflicterende criteria.Dual Sliderst.select_sliderBepaalt de kleur-overlay van je grafiek (bijv. oranje voor cyclisch, paars voor defensief).

Een klein stukje "Analisten-Magie" voor de code:Om die conflicten in de checkboxes goed te regelen, kun je dit patroon gebruiken:
st.subheader("Strategie Validatie")
high_div = st.checkbox("Focus op Hoog Dividend (>5%)")
high_growth = st.checkbox("Focus op Hyper-growth (>20% omzetstijging)")

if high_div and high_growth:
    st.error("⚠️ Conflict: Bedrijven met >20% groei keren zelden >5% dividend uit. Je filtert waarschijnlijk alle resultaten weg.")







