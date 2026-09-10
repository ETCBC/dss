import { sql,SQL } from "bun"

const dbCACCHT = new SQL({
    // Required for MySQL when using options object
    adapter: "mysql",
    socket: "/tmp/mysql.sock",
    database: "yourDatabase",//supply your own credentials
    username: "yourUsername",
    password: "yourPassword",
    allowPublicKeyRetrieval: true,//for local unsecure connections
    onclose: (client,error) => {
        if(error)
            console.error("MSQL connection error:",error)
        //else
            //console.log("gesloten")
    }
})

function matchWoorden(woorden1,woorden2,match){
    const subs = []
    let teller = 0
    const w2Entr = Array.from(woorden2.entries())
    //vind langste substrings matches
    woorden1.forEach((w1,i1) => {
        const nog1 = woorden1.length - i1
        //find substring
        const sub = w2Entr.filter(([,w2]) => match(w1,w2)).map(([i2,]) => {//alle gematchte woorden
            const len2 = Math.min(woorden2.length - i2,nog1)
            for(let t = 1; t < len2; t++)//volgende woorden testen en aan substr toevoegen
                if(!match(woorden1[i1+t],woorden2[i2+t]))//volgende woord matcht niet meer, substring gevonden
                    return {index1:i1,index2:i2,length:t}
            return {index1:i1,index2:i2,length:len2}//substring loopt tot einde zin
        }).reduce((currentM,item) => item.length > currentM.length ? item : currentM, {length:0})//vind langste substring

        if(sub.length && sub.length >= teller)
            subs.push(sub)
        
        teller = sub.length
    })

    //check op overlap
    return filterOverlap(subs)
}

function filterOverlap(subs){
    const sortLI = (a,b) => b.length - a.length || a.index1 - b.index1//sorteer op lengte, index
    const checkOverlap = (a,b,c,ns,start) => {
        let overlap = 0
        if(a <= b && b < c){
            if(start){
                overlap = c - b
                ns.index1 += overlap
                ns.index2 += overlap
            }else
                overlap = b - a + 1
            ns.length -= overlap
        }
    }
    subs.sort(sortLI)
    let sub,fSubs = []
    while(sub = subs.shift()){
        const {index1,index2,length} = sub
        if(length <= 0)
            break
        //overlap bij andere subs van deze sub verwijderen
        subs.forEach(ns => {
            checkOverlap(index1,ns.index1,index1 + length,ns,true)//begin ns woorden1 ligt binnen deze, begin verwijderen
            checkOverlap(index1,ns.index1 + ns.length - 1,index1 + length,ns)//eind ns woorden 1 ligt binnen deze, eind verwijderen
            checkOverlap(index2,ns.index2,index2 + length,ns,true)//begin ns woorden2 ligt binnen deze, begin verwijderen
            checkOverlap(index2,ns.index2 + ns.length - 1,index2 + length,ns)//eind ns woorden 2 ligt binnen deze, eind verwijderen
        })
        subs.sort(sortLI)
        fSubs.push(sub)
    }
    fSubs.sort((a,b) => a.index1 - b.index1)//sorteer op index

    return fSubs
}

function stripToCons(str){
    return str.replaceAll(/((\&[A-Z<>]{1})|(\:[a-z]{1})|[\(\+\/\[\]\!\~\-]+)/g,'')
}

function removeML(str){
    return str.replaceAll(/((\&[A-Z<>]{1})|\()/g,'')
}

let Q = []
async function insert(){
    console.log(Q.length + 'rijen invoegen')
    await dbCACCHT`INSERT INTO dss ${sql(Q)} ON DUPLICATE KEY UPDATE correct=VALUES(correct),bhs=VALUES(bhs)`
    Q.length = 0
}

async function checkAlign(bhs,etcbc){
    const matches = matchWoorden(etcbc,bhs,(w1,w2) => {
        return w1.cons == w2.cons || w1.parsing==w2.morf || stripToCons(w1.parsing)==stripToCons(w2.morf)
    })

    for(const {index1,index2,length} of matches){
        const etcbcSl = etcbc.slice(index1,index1+length)
        const bhsSl = bhs.slice(index2,index2+length)
        for(let i=0;i<length;i++){
            const w1 = etcbcSl[i]
            const w2 = bhsSl[i]
            if(w1.parsing==w2.morf || removeML(w1.parsing)==removeML(w2.morf) && !/(\&[A-Z<>]{1}[\/\[\]\!\-\~]{1,2}[A-Z<>]+)|([A-Z<>]+[\/\[\]\!\-\~]{1}\&)/g.exec(w1.parsing))
                Q.push({
                    id:w1.id,
                    correct:1,
                    bhs:w2.morf
                })
            else
                Q.push({
                    id:w1.id,
                    correct:null,
                    bhs:w2.morf
                })
        }
    }

    if(Q.length > 500)
        await insert()
}

const etcbcAll = await dbCACCHT.unsafe("SELECT dss.id,vid,cons,parsing FROM dss JOIN 1Qisaa ON dss.id=1Qisaa.id ORDER BY id")
const etcbcPV = Object.groupBy(etcbcAll,r => r.vid)
const bhsAll = await dbCACCHT.unsafe("SELECT * FROM bhs_ref WHERE vid BETWEEN 23000000 AND 24000000 ORDER BY vid,Woord")
const bhsPV = Object.groupBy(bhsAll,r => r.vid)

for(const vid in etcbcPV){
    await checkAlign(bhsPV[vid],etcbcPV[vid])
}
if(Q.length)
    await insert()

console.log("Klaar")