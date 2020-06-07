# coding: utf-8

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

#_______get all missions'urls from a list of search results_______
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
headers = {'User-Agent': user_agent}
urls=[]

url = input("Entrez l'url à scraper :")
end_url=url.replace('https://www.tousbenevoles.org/trouver-une-mission-benevole?', '')
pages=int(input("Entrez le nombre de pages de résultats :"))

for i in range(1,pages+1):
  r = requests.get('https://www.tousbenevoles.org/trouver-une-mission-benevole?page='+str(i)+'&'+end_url, headers=headers)
  page_contenu = BeautifulSoup(r.text, 'html.parser')
  url=[element['href'] for element in page_contenu.find_all('a', attrs={'class':'infos'})]
  urls=urls+url

print('Nous avons trouvé '+str(len(urls))+' missions')

#_______scrap structure's name & address + mission details_______
"""
for each item to scrap, process is in 3 parts : 
  collect html info through the appropriate tag
  extract & customize desired text
  append results in final list
"""
structure=[]
address=[]
title=[]
descr=[]
add_info=[]
skills=[]
availability=[]
mission_type=[]
public_mission=[]
mission_duration=[]
update_date=[]

compteur=1
print('Missions scrapées :')
for url in urls:
    r = requests.get(url, headers=headers)
    r.encoding= 'utf-8'
    all_page = BeautifulSoup(r.text, 'html.parser')

    names = all_page.find_all('h2')
    names=names[0].text.strip().replace('Mission proposée par ', '').split('\n')[0]
    structure.append(names)

    adr_page = all_page.find_all('div', attrs={'id':'show_lieu_mission'})
    adr_page=adr_page[0].find_all('li')[0].text.strip().replace('\t','').split('\n')
    adresses=[i for i in adr_page if i not in ['', ' ']]
    adresses=';'.join(adresses)
    address.append(adresses)

    title_mission = all_page.find_all('h1')[0].text
    title.append(title_mission)

    descr_mission = all_page.find_all('p', attrs={'class':'justify'})
    descr_mission = descr_mission[0].text.replace("Covid-19 : candidats bénévoles, assurez-vous auprès de l’association que vous contactez que la mission est compatible avec les règles sanitaires édictées par le gouvernement.", '')
    descr.append(descr_mission)

    various_info = all_page.find_all('div', attrs={'class':'panel-body'})
    infos = various_info[0].text.strip()
    add_info.append(infos)

    comp = various_info[1].text.strip()
    skills.append(comp)

    dispo = various_info[2].text.strip()
    availability.append(dispo)

    typ = all_page.find_all('a', attrs={'class':'iframe'})
    typ = typ[0].text
    mission_type.append(typ)

    public = all_page.find_all('a', attrs={'title':'Les types de publics'})
    public = [item.text for item in public]
    public = ''.join(public).strip()
    public_mission.append(public)

    li_tags = all_page.find_all('li')
    #mission_duration has no specific tag but is always before 'MAJ' text, so we will get index of 'MAJ' text and use the text just before this
    ind=[li_tags.index(i) for i in li_tags if re.search('MAJ', i.text)][0] - 1
    duree = li_tags[ind].text
    mission_duration.append(duree)

    maj = [i.text for i in li_tags if re.search('MAJ', i.text)]
    maj = maj[0].replace('MAJ :  ', '')
    update_date.append(maj)

    print(compteur)
    compteur+=1
    
#_______export mails and phone details_______
"""
mails and phones are shown on the webpage through a php call, needing the mission ID and structure ID
So we first extract those informations and then scrap
"""

#get mission ids
ids=[url[-5:] for url in urls]
ids=[re.sub('\D', '', id) for id in ids]
ids=[id[1:] if id[0]=='0' else id for id in ids]

#get structure ids
ids_assoc=[]
for url in urls:    
    r = requests.get(url, headers=headers)
    r.encoding= 'utf-8'
    page_contenu = BeautifulSoup(r.text, 'html.parser')
    id_assoc = page_contenu.find_all('h2')
    id_assoc=id_assoc[0].find_all('a')[0]['href'][-5:]
    ids_assoc.append(id_assoc)
ids_assoc=[re.sub('\D', '', id) for id in ids_assoc]
ids_assoc=[id[1:] if id[0]=='0' else id for id in ids_assoc]

#scrap mails/phones
def get_phone_mail(url, params):
  """ to extract phone or mail from a php link"""
  response=requests.post(url, data=params, headers=headers)
  soup = BeautifulSoup(response.text, 'html5lib')
  extract=soup.find_all('body')[0].text.strip()
  extract=None if extract=='nop' else extract
  return extract

contact_phone=[]
assoc_phone=[]
mail_contact=[]
mail_responsible=[]

compteur=1
print('Missions scrapées :')

for id_annonce, id_ass in zip(ids, ids_assoc):
  mails=get_phone_mail('https://www.tousbenevoles.org/services/action/action.php', {'action':'show','quoi':'action', 'field':'action_email', 'id':id_annonce, 'from':'action', 'from_id':id_annonce})
  mail_contact.append(mails)

  mails=get_phone_mail('https://www.tousbenevoles.org/services/association/association.php', {'action':'show','quoi':'association', 'field':'responsible_email', 'id':id_ass, 'from':'action', 'from_id':id_annonce})
  mail_responsible.append(mails)

  phones=get_phone_mail('https://www.tousbenevoles.org/services/action/action.php', {'action':'show','quoi':'action', 'field':'contact_tel', 'id':id_annonce, 'from':'action', 'from_id':id_annonce})
  contact_phone.append(phones)

  phones=get_phone_mail('https://www.tousbenevoles.org/services/association/association.php', {'action':'show','quoi':'association', 'field':'assoc_phone', 'id':id_ass, 'from':'action', 'from_id':id_annonce})
  assoc_phone.append(phones)

  print(compteur)
  compteur+=1

#_______export missions to excel_______
scrap = pd.DataFrame({'link':urls, 'structure': structure, 'address':address,  'contact_phone':contact_phone, 'assoc_phone':assoc_phone, 'mail_contact':mail_contact, 'mail_responsible':mail_responsible, 'title':title, 'descr':descr, 'add_info':add_info, 'skills':skills, 'availability':availability, 'mission_type':mission_type, 'public_mission':public_mission, 'mission_duration':mission_duration, 'update_date':update_date})
scrap['date_scrap']=pd.to_datetime("today").date()
scrap.to_excel(r'scrap_tousbenevoles_missions.xlsx', index=False) #insert appropriate file path
