import json
meta=json.load(open('vid/steps_meta.json'));sp=json.load(open('vid/sprite_meta.json'))
M={m['n']:m for m in meta}
def P(x,y,k):return {'x':x,'y':y,'k':k}
# manual corrections (coordinates normalised to each crop)
M[2]['pts']=[P(.641,.396,'testa')]+[p for p in M[2]['pts'] if p['k'] in('piede dietro',)]
M[7]['pts']=[p for p in M[7]['pts'] if p['k'] in('testa','piede esterno')]+[P(.50,.755,'ginocchio a terra'),P(.547,.667,'mani')]
M[8]['pts']=[p for p in M[8]['pts'] if p['k'] in('testa','piede esterno')]+[P(.5625,.708,'ginocchio a terra')]
S=[
{'n':1,'t':28.75,'vista':'Laterale','titolo':'Guardia e distanza',
 'vede':'Entrambi in guardia con le ginocchia piegate e la schiena inclinata in avanti ma dritta. Il ragazzo in verde, a destra, ha il piede destro avanti e il sinistro dietro. Le mani sono davanti, all\'altezza dei fianchi, quasi a contatto con quelle dell\'allenatore in nero, a sinistra: il braccio non è del tutto teso.',
 'dice':'«Siamo in una buona guardia. Voglio essere abbastanza vicino da toccarlo, con il braccio non del tutto esteso, ma sparare da lontano.»',
 'perche':'Se sei troppo lontano devi coprire troppo spazio. Se sei troppo vicino lui può bloccarti o colpirti. Toccare il suo braccio è il modo per controllare la distanza.'},
{'n':2,'t':29.5,'vista':'Laterale','titolo':'Abbassa il livello',
 'vede':'In meno di mezzo secondo il ragazzo piega le ginocchia e porta il busto in avanti e in basso. La testa scende sotto il livello delle mani dell\'allenatore. Il piede dietro resta teso e spinge sul tappeto.',
 'dice':'«Primo passo: abbasso il livello.»',
 'perche':'Le braccia dell\'avversario sono ciò che ti blocca. Passandoci sotto non le incontri. Si scende con le ginocchia, non piegando la vita.'},
{'n':3,'t':30.0,'vista':'Laterale','titolo':'Il piede davanti entra tra le sue gambe',
 'vede':'La gamba davanti parte verso le gambe dell\'allenatore, mentre quella dietro resta lunga e spinge. Il busto rimane basso e le mani restano tese davanti, vicino alle sue. L\'immagine è un po\' sfocata perché il movimento è rapido.',
 'dice':'«Faccio un passo profondo in mezzo alle sue gambe.»',
 'perche':'Il passo si fa con la gamba davanti, che è già avanti e arriva prima. Il piede dietro carica la spinta.'},
{'n':4,'t':30.5,'vista':'Laterale','titolo':'Sotto le sue mani',
 'vede':'La testa del ragazzo arriva all\'altezza delle anche dell\'allenatore, il ginocchio davanti è vicino alla sua gamba, il piede dietro è disteso all\'indietro. Le mani dell\'allenatore toccano il ragazzo, ma lui è già sotto.',
 'dice':'«Secondo passo: parte l\'attacco, entro.»',
 'perche':'I due passi (abbassare, entrare) sono separati: prima il livello, poi il passo. Se il passo parte alto, le braccia dell\'avversario lo fermano.'},
{'n':5,'t':33.0,'vista':'Obliqua (la camera si è spostata)','titolo':'Dentro, con un ginocchio a terra',
 'vede':'Il ragazzo è dentro: il ginocchio davanti è appoggiato al tappeto tra i piedi dell\'allenatore, l\'altro piede è appoggiato di lato e la testa è accanto al suo fianco. Le braccia vanno in basso verso le sue gambe.',
 'dice':'«Il ginocchio sale, siamo dentro.»',
 'perche':'Con il ginocchio a terra hai una base bassa e stabile. La testa a lato e non davanti ti protegge e sposta il suo peso.'},
{'n':6,'t':36.0,'vista':'Obliqua','titolo':'Anche alte, testa alta, mani dietro i polpacci',
 'vede':'Il busto è più dritto e la testa alta, appoggiata al fianco dell\'allenatore. Le braccia avvolgono le sue gambe sotto il ginocchio. Il ragazzo guarda nella direzione in cui andrà.',
 'dice':'«Le mie anche sono alte, la mia testa è alta, guardo dove spingerò. Le mani sono dietro i suoi polpacci.»',
 'perche':'Con schiena dritta e testa alta lo scheletro regge il peso, non i muscoli. Le mani dietro i polpacci tirano le sue gambe verso di te.'},
{'n':7,'t':46.0,'vista':'Da dietro l\'allenatore','titolo':'La presa dietro la gamba, il piede esterno',
 'vede':'Da questa inquadratura si vede bene: il ragazzo è con un ginocchio a terra tra i piedi dell\'allenatore, l\'altro piede appoggiato largo, di lato. La testa è a destra dell\'anca dell\'allenatore, le mani sono dietro la sua gamba. Resta in questa posizione per diversi secondi, in lento.',
 'dice':'«Quando finisco, spazzo un po\' la gamba verso l\'esterno.»',
 'perche':'Il piede largo e di lato prepara il cambio di direzione: non spingi dritto, spingi di lato.'},
{'n':8,'t':49.5,'vista':'Da dietro l\'allenatore','titolo':'Il piede sale: un passo grande',
 'vede':'Il peso si sposta: il piede che era a terra con il ginocchio si pianta accanto ai piedi dell\'allenatore, mentre l\'altro piede resta largo. Il ragazzo sta per essere su due piedi, con la testa alta e il busto dritto.',
 'dice':'«Passo in alto, grande.»',
 'perche':'Per spingere con tutta la potenza servono entrambe le gambe a terra: il ginocchio non resta giù.'},
{'n':9,'t':50.25,'vista':'Obliqua, in movimento','titolo':'Gira l\'angolo e spingi',
 'vede':'Il ragazzo spinge con la gamba dietro, che è tesa, e gira. L\'allenatore ha già perso l\'appoggio: un piede è in aria e il corpo si sta girando in orizzontale. L\'azione dura meno di mezzo secondo.',
 'dice':'«Giro l\'angolo.»',
 'perche':'La rotazione avviene verso il lato della testa. Senza la testa a lato e le gambe tirate verso di te non gira.'},
{'n':10,'t':51.0,'vista':'Obliqua, a terra','titolo':'Atterraggio sopra e controllo',
 'vede':'Il ragazzo atterra sopra l\'allenatore, con le ginocchia aperte e il petto sul suo busto. Dopo l\'atterraggio le mani controllano il suo torso (la guida del video non dice altro su questa parte).',
 'dice':'La guida non commenta l\'atterraggio.',
 'perche':'Il punto arriva con il controllo, non con la caduta: dopo l\'atterraggio non si lascia andare.'}]
for s in S:s['pts']=M[s['n']]['pts']
data={'steps':S,'sp':sp}
html=open('page_template.html').read().replace('/*DATA*/null',json.dumps(data,ensure_ascii=False))
open('/home/user/claude/libretto-lotta/doppia/index.html','w').write(html);print(len(html))
