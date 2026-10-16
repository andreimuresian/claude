# Genera libretto-lotta/index.html unendo i dati delle tecniche (doppia gamba + seatbelt toss).
# Uso: python3 gen_libretto.py <cartella con vid/steps_meta.json, vid/sprite_meta.json della doppia> <cartella seatbelt con steps_meta.json, sprite_meta.json>
import json,sys,re,os
dv,sv,fv=sys.argv[1],sys.argv[2],sys.argv[3]
src=open(os.path.join(os.path.dirname(__file__),'gen_html.py')).read().split('for s in S:')[0]
src=src.replace("'vid/steps_meta.json'",repr(dv+'/vid/steps_meta.json')).replace("'vid/sprite_meta.json'",repr(dv+'/vid/sprite_meta.json'))
ns={};exec(src,ns)
for s in ns['S']:s['pts']=ns['M'][s['n']]['pts']
doppia={'id':'doppia','nome':'Doppia gamba','titolo':'Doppia gamba, passo per passo','dir':'doppia','sp':ns['sp'],'steps':ns['S'],
 'lead':'Dieci fotogrammi reali del tiro alla doppia gamba, con ciò che si vede, ciò che dice l\'istruttore e il perché.',
 'leggi':'Il ragazzo in maglia verde, a destra, esegue la tecnica. L\'allenatore in nero, a sinistra, la subisce. I cerchi numerati indicano testa, mani, ginocchia e piedi del ragazzo che attacca. <b>Attenzione alla vista:</b> solo i passaggi 1-4 sono ripresi di lato; poi la camera si sposta e ogni foto dice da dove è ripresa.',
 'nota':'I passaggi 9 e 10 sono sfocati perché il movimento è veloce.'}
M={m['n']:m for m in json.load(open(sv+'/steps_meta.json'))}
sp=json.load(open(sv+'/sprite_meta.json'))
CT={1:58.5,2:59.1,3:60.0,4:60.5,5:60.75,6:61.0,7:62.0,8:62.5,9:63.0,10:63.75,11:64.0,12:64.6}
L='Laterale'
ST=[
{'n':1,'t':18.25,'titolo':'Guardia e inizio del tiro',
 'vede':'Kolat (maglia gialla, a destra) è in guardia bassa: ginocchia piegate, schiena inclinata in avanti, le mani davanti ai fianchi, aperte. Un piede è più avanti, vicino all\'avversario in nero, l\'altro è dietro. Lui è appena partito: non ha ancora toccato nessuno.',
 'dice':'«Faccio il mio tiro alla single leg.» Il video parte da quando la single leg è già stata fatta e l\'avversario difende.',
 'perche':'Il seatbelt toss non è un attacco da fermo: è un secondo tempo, che usi quando la single leg si blocca. Per questo il video parte dal tiro.'},
{'n':2,'t':19.5,'titolo':'Contatto: l\'avversario fa il whizzer',
 'vede':'I due si toccano. L\'avversario passa un braccio sopra la spalla di Kolat e lo preme verso il basso; Kolat tiene la testa sotto il suo petto e le mani cercano le sue gambe. I piedi dell\'avversario si stringono e la gamba è appena sollevata.',
 'dice':'«Lui fa il whizzer.» Il whizzer è il braccio che passa sopra la spalla dell\'attaccante e lo schiaccia verso il tappeto.',
 'perche':'È la difesa classica alla single leg: con il whizzer l\'avversario ti appesantisce la spalla e non ti lascia salire. Da qui in poi Kolat non può più rialzarsi dritto con facilità.'},
{'n':3,'t':21.0,'titolo':'Single leg con un ginocchio a terra',
 'vede':'Kolat è abbassato su un ginocchio appoggiato al tappeto e tiene la gamba dell\'avversario con entrambe le mani, vicino al ginocchio. La sua testa è premuta contro le costole dell\'avversario; il braccio dell\'avversario è sopra la sua schiena. Il piede dell\'avversario resta a terra tra le gambe di Kolat.',
 'dice':'«Cerca di tenere il piede dentro il mio cavallo. Non vuole che lo porti fuori, sull\'anca o dentro.»',
 'perche':'Finché il piede dell\'avversario resta tra le tue gambe, la gamba non esce: lui ha una base e tu non puoi sollevarla. Lo scopo della tecnica è risolvere questo stallo.'},
{'n':4,'t':24.0,'titolo':'Lo stallo: Kolat si alza, la gamba resta bloccata',
 'vede':'Kolat è di nuovo in piedi, piegato in avanti, con la testa contro il torace dell\'avversario. Le mani sono unite dietro la gamba catturata, che resta ripiegata sotto il suo braccio. L\'avversario sta su un piede solo, con la schiena inclinata in avanti, il braccio libero penzola verso il tappeto.',
 'dice':'«Siamo bloccati in questa posizione. Non riesco a far uscire il piede. Tutto ciò che voglio fare ora è salire.»',
 'perche':'Non spingere né tirare a vuoto: se il piede non esce, il piano è salire lungo il corpo dell\'avversario fino a un\'altra presa. È questa la decisione chiave della tecnica.'},
{'n':5,'t':28.0,'titolo':'Salire con la mano, in profondità',
 'vede':'La testa di Kolat resta premuta contro l\'avversario. La mano sale lungo la gamba catturata, dalla caviglia verso il ginocchio; l\'altra mano la accompagna. I piedi di Kolat restano fermi e larghi, le ginocchia piegate: sale con le mani, non alzandosi in piedi.',
 'dice':'«Prendo questa mano e salgo, vado in profondità dietro il ginocchio.»',
 'perche':'Più la mano è profonda dietro il ginocchio, più la gamba è controllata e meno spazio ha lui per ritrarla. Si sale con le mani perché la schiena non si deve sollevare e il whizzer non deve prendere spazio.'},
{'n':6,'t':30.5,'titolo':'Avvolgere dietro il ginocchio',
 'vede':'Il braccio di Kolat passa dietro il ginocchio dell\'avversario e si chiude: il ginocchio dell\'avversario è ora nell\'incavo del braccio. La testa è ancora sotto il suo petto e i piedi di Kolat sono rimasti dove erano.',
 'dice':'«Una volta che ho avvolto, adesso posso cambiare.»',
 'perche':'La gamba è controllata dal gomito, non solo dalla mano. Solo ora si può lasciare la presa di prima senza che l\'avversario la ritragga: il cambio si fa quando la gamba è già al sicuro.'},
{'n':7,'t':34.5,'titolo':'Il cambio verso il seatbelt',
 'vede':'Le mani di Kolat si uniscono e la gamba è tenuta con la mano e l\'avambraccio. Un braccio comincia a passare attorno al busto dell\'avversario, ancora sotto la sua ascella. Il corpo di Kolat non si è mosso: cambiano solo le braccia.',
 'dice':'«Posso cambiare e andare alla seatbelt.»',
 'perche':'Il cambio è la parte che richiede tempo, perché le braccia lasciano una presa per prenderne un\'altra. Si fa da fermi e a testa premuta, per non dargli il tempo di scappare.'},
{'n':8,'t':40.0,'titolo':'Seatbelt: braccio attorno al busto, profondo',
 'vede':'Il braccio di Kolat è passato attorno alla vita dell\'avversario e l\'altro braccio completa la presa, come una cintura di sicurezza. La testa di Kolat è contro le sue costole, il peso in avanti. L\'avversario ha ancora un piede a terra e una mano appoggiata al proprio ginocchio.',
 'dice':'«Così profondo: ho la seatbelt.»',
 'perche':'Una presa profonda attorno al busto serve a farlo caricare sulle tue anche quando ti giri. Se la presa è superficiale, nell\'arco si scivola via.'},
{'n':9,'t':40.75,'titolo':'Passo inverso: il piede attraversa il suo corpo',
 'vede':'Kolat sposta un piede con un passo largo, di taglio, davanti al corpo dell\'avversario, e inizia a girarsi: il busto passa da frontale a dorso verso la camera. Il piede che passa è quello dietro. Le braccia restano chiuse attorno al busto.',
 'dice':'«Faccio un passo inverso. Prendo questa gamba e voglio passare attraverso il suo corpo, per l\'arco all\'indietro.»',
 'perche':'Il passo porta le tue anche sotto le sue. Se il piede non attraversa abbastanza, hai la schiena davanti al suo petto, non sotto.'},
{'n':10,'t':41.25,'titolo':'Anche sotto di lui, ginocchia piegate',
 'vede':'Kolat è ora di schiena alla camera, accovacciato con le ginocchia aperte e i piedi larghi. L\'avversario è piegato sopra la sua schiena, con le gambe che stanno ormai lasciando il tappeto. Il busto di Kolat è completamente girato.',
 'dice':'«Ora faccio l\'arco.»',
 'perche':'Ti accovacci per metterti sotto di lui, poi lo sollevi spingendo le anche in avanti e verso l\'alto, non tirando con le braccia.'},
{'n':11,'t':41.55,'titolo':'L\'arco: lui passa sopra la schiena',
 'vede':'Un solo istante, sfocato: l\'avversario è sollevato sopra la schiena di Kolat, con le gambe in aria. Kolat ha i piedi ancora larghi e ben piantati.',
 'dice':'«Poi l\'arco.»',
 'perche':'La spinta vera si fa con le gambe e le anche, che si distendono in un movimento solo.'},
{'n':12,'t':42.0,'titolo':'Atterraggio: lui sulla schiena, Kolat sopra',
 'vede':'L\'avversario sta cadendo di schiena, con le gambe in aria, e Kolat è sopra di lui, con le braccia ancora attorno al busto. La caduta dura meno di mezzo secondo.',
 'dice':'La trascrizione si ferma qui: nel video seguono azioni dal vivo.',
 'perche':'Il punto più alto è il lancio, ma la tecnica finisce quando atterri sopra, in controllo. Un seatbelt toss ben fatto dà punti e posizione.'}]
for s in ST:s['pts']=M[s['n']]['pts'];s['vista']=L;s['ci']=1;s['ct']=CT[s['n']]
sb={'id':'seatbelt','nome':'Seatbelt toss','titolo':'Seatbelt toss, passo per passo','dir':'seatbelt','sp':sp,'steps':ST,
 'lead':'Dodici fotogrammi reali del seatbelt toss di Cary Kolat: una single leg che si blocca contro un whizzer e si trasforma in un lancio con l\'arco.',
 'leggi':'Kolat, in maglia gialla a destra, esegue la tecnica. L\'avversario, in nero a sinistra, la subisce. La camera è sempre ferma e di lato, quindi tutti i passaggi sono ripresi dalla stessa vista. I fotogrammi grandi vengono dalla dimostrazione lenta dell\'istruttore; il lettore in alto mostra invece solo le ripetizioni fluide, senza la parte in cui spiega, e «Vedi nel video» porta al momento corrispondente della seconda ripetizione (i tempi coincidono solo in modo approssimato). I cerchi numerati indicano testa, mani, piedi e ginocchio di Kolat.',
 'nota':'Nel video l\'istruttore dice che questa tecnica vale «3, a volte 5» punti, secondo l\'arco. Il lato (destro o sinistro) di piedi e braccia non è confermato dalla trascrizione: nelle descrizioni uso «un piede» e «il piede dietro» invece di inventare un lato.'}
FT=[
(76.0,0,'Primo piano','Presa interna: il braccio dentro, il pollice come un amo',
 'Spencer Lee (maglia grigia e pantaloni neri) e il compagno (maglia nera, scarpe rosse) sono in piedi, vicini. Lee porta un braccio dentro il braccio del compagno e ne afferra l\'avambraccio. L\'etichetta gialla del video segna la mano.',
 '«Mi piace avere una presa interna con il braccio sinistro, visto che sono destro. Quando afferri il suo braccio il pollice non sta qui: è come un amo da pesca.»',
 'Una presa interna ti dà controllo del suo braccio senza lasciarti coprire. Il pollice «a amo» chiude la presa con le dita: così è più forte e meno facile da staccare.'),
(90.0,0,'Laterale','Batti la sua testa con la tua',
 'Visti di lato: il compagno è piegato in avanti, con la testa bassa; Lee è quasi dritto davanti a lui, con una mano sulla sua spalla e la testa vicina alla sua. L\'etichetta nel video dice «Beat opponent\'s head».',
 '«Vuoi che la tua testa batta la sua. Battere la sua testa vuol dire avere la tua testa sulla sua tempia, o la sua testa che gira da un\'altra parte: non fronte contro fronte né orecchio contro orecchio.»',
 'Chi vince la posizione della testa decide dove si va. Se la tua testa è sulla sua tempia, la sua spalla è bloccata e tu hai la strada libera per cambiare livello.'),
(102.0,0,'Da dietro il compagno','Mano destra appoggiata sulla sua spalla',
 'Lee tiene l\'altra mano appoggiata sulla spalla o sul collo del compagno (il segno giallo del video la indica). La testa di Lee è accanto a quella del compagno, il busto inclinato in avanti.',
 '«Mi piace tenere la mano destra così, appoggiata. Anche se lui ha una presa esterna su di me non importa, perché lo scopo è battere la sua testa con la mia e poter cambiare livello per il mio tiro.»',
 'La mano appoggiata fa da punto d\'appoggio: puoi spingere via o tirare, e allo stesso tempo tieni lontano le sue mani dalla tua testa.'),
(107.0,0,'Primo piano','Mani tese e forti, testa contro testa',
 'Primo piano di entrambi: le braccia sono incrociate in una presa dentro-dentro, le teste sono vicine e Lee spinge in avanti con tutto il corpo. Le ginocchia del compagno sono leggermente piegate.',
 '«Mani strette e forti, e lo batti. Per tutto il tempo premo in avanti.»',
 'La pressione continua è ciò che fa reagire l\'avversario. Se smetti di spingere, lui riprende la sua posizione.'),
(118.0,0,'Dall\'alto','Pressione in avanti, poi cambio di livello',
 'Vista dall\'alto: Lee spinge verso il compagno (freccia gialla «Pressure forward») e il compagno si abbassa leggermente (freccia «Level change»). Le teste restano a contatto.',
 '«Sono sempre in pressione in avanti, e poi puoi lasciar cadere il tiro.»',
 'Prima si spinge, poi si scende. Il cambio di livello avviene mentre l\'altro è spinto in avanti e non riesce a seguirti.'),
(126.0,1,'Laterale','Fai reagire: lo spingi e lui spinge indietro',
 'Lee spinge in avanti con la fronte e la presa, il compagno risponde spingendo all\'indietro. L\'etichetta nel video dice «Bait opponent into pressuring back».',
 '«Quando muovi molto un avversario, tende a reagire con forza. Appena reagisce, cade sopra di me: è la reazione che vuoi. Uno sopra di te, perché ti dà una grande sensazione dell\'altro.»',
 'Il fireman\'s carry usa la sua reazione: se spinge indietro, il suo peso è in avanti e tu ci passi sotto.'),
(138.0,1,'Dall\'alto','Girare sotto di lui',
 'Vista dall\'alto: Lee gira in cerchio (freccia gialla), mentre il compagno si muove con i piedi per seguirlo.',
 '«Vedi come i suoi piedi si muovono? Io giro sotto di lui.»',
 'Girare sotto di lui lo costringe a muovere i piedi e a perdere l\'equilibrio, mentre tu resti sotto il suo peso.'),
(152.0,1,'Laterale','Piccole finte',
 'Lee è chinato in avanti con una mano allungata e l\'altra vicino al corpo: una finta piccola, con la testa e la mano. Il compagno è di fronte, con le mani sulle ginocchia. Etichetta: «Bait opponent with small fakes».',
 '«Una finta non deve essere per forza grande. Può bastare muovere la testa a destra e li spaventi. Lo stesso per il setup del fireman: un piccolo movimento, e lui reagisce. Poi spingi dentro.»',
 'Una finta piccola costa poca energia e non ti sbilancia, ma basta a far reagire l\'avversario.'),
(186.0,2,'Laterale','Mano destra appoggiata o fuori',
 'Lee e il compagno sono in presa interna; la mano libera di Lee è sopra la spalla del compagno. L\'etichetta nel video dice «Right hand posted or outside».',
 '«Questa mano può stare appoggiata sulla spalla così, oppure all\'esterno come la presa interna: va bene anche così. Non mi dà fastidio avere due mani dentro. Penso che vadano bene tutte, perché qui posso staccarmi da lui.»',
 'Non importa quale presa usi, purché sia forte e tu abbia la posizione della testa.'),
(196.0,2,'Dall\'alto','Spingere o tirare per cambiare livello',
 'Vista dall\'alto: il compagno è in piedi piegato, Lee è abbassato davanti a lui con le mani sul suo corpo. L\'etichetta dice «Push or pull to level change».',
 '«Posso spingerlo via, e poi cambiare livello; all\'esterno posso comunque spingere e tirare.»',
 'Spingere o tirare serve a creare lo spazio per scendere. Se non c\'è spazio, non scendi.'),
(207.6,2,'Dall\'alto','Enfatizza il movimento',
 'Vista dall\'alto: i due sono in presa con le teste a contatto e Lee in leggero movimento di lato; l\'etichetta dice «Emphasize movement».',
 '«Penso che non conti tanto che presa sia, purché ci sia una presa forte dentro e la posizione della testa. Tutto ruota intorno al movimento: piccoli movimenti, sempre pressione in avanti e girando in cerchio, e poi esplodi nel tiro.»',
 'Il setup non è una posizione ferma: sono piccole spinte, finte e giri. L\'attacco parte quando l\'altro reagisce.'),
(223.6,3,'Dall\'alto','Dove porta il setup: il tiro',
 'Dal basso nel video si vede il risultato: Lee ha già eseguito il tiro e il compagno è a terra, di schiena, con Lee sopra. Questa parte non è spiegata nella trascrizione.',
 'La trascrizione si ferma qui: «Questo è il mio setup per il fireman\'s carry.» Il tiro è spiegato nella parte successiva.',
 'Il tiro stesso non è in questo video: qui si studia il setup, cioè come arrivare nella posizione giusta.')]
F=[{'n':i+1,'t':t,'ci':c,'vista':v,'titolo':ti,'vede':ve,'dice':d,'perche':p} for i,(t,c,v,ti,ve,d,p) in enumerate(FT)]
for s in F:s['h']=540;s['pts']=[]
fm=json.load(open(fv+'/sprite_meta.json'))
fire={'id':'fireman','nome':'Fireman\'s carry: setup','titolo':'Fireman\'s carry, il setup','dir':'fireman','sp':fm,'steps':F,
 'lead':'La preparazione al fireman\'s carry spiegata da Spencer Lee: presa interna, posizione della testa, pressione in avanti, finte e cambio di livello.',
 'leggi':'Spencer Lee è in maglia grigia e pantaloni neri; il compagno è in maglia nera con scarpe rosse. Il video cambia spesso inquadratura (laterale, da dietro, dall\'alto, primo piano), quindi ogni foto indica la vista. Le scritte in inglese sono quelle del video. Non ci sono cerchi sulle foto: il video ha già le sue etichette.',
 'nota':'Questo video mostra solo la preparazione: il tiro vero e proprio sarà nella parte 2. Il lettore in alto mostra solo le parti con la dimostrazione (senza il parlato in primo piano), in quattro spezzoni.'}
tpl=open(os.path.join(os.path.dirname(__file__),'libretto_template.html')).read()
out=tpl.replace('/*DATA*/null',json.dumps({'techs':[doppia,sb,fire]},ensure_ascii=False))
open(os.path.join(os.path.dirname(__file__),'..','index.html'),'w').write(out);print(len(out))
