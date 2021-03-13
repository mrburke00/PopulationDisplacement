from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import argparse
import json
import glob
import os
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


parser = argparse.ArgumentParser()

parser.add_argument('--config',
                    dest='config',
                    required=True,
                    help='JSON config file')

parser.add_argument('--cred',
                    dest='cred',
                    required=True,
                    help='JSON credential file')

parser.add_argument('--dryrun',
                    dest='dry_run',
                    action='store_true')

args = parser.parse_args()

cred = json.load(open(args.cred))
config = json.load(open(args.config))

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1200x600')
options.add_argument('window-size=1200x600')

#driver = webdriver.Chrome(chrome_options=options)
driver = webdriver.Chrome('/Users/DBurke/Documents/Layerlab/generalized_pipeline/automate_download/chromedriver') 
#driver = webdriver.Chrome(executable_path=os.path.abspath("Users/DBurke/Documents/Layerlab/automate_download/chromedriver"))
url2="https://www.stackoverflow.com"
url1="https://www.google.com"
first = True
for m in config['maps']:
    print(m)
    repo = [ ''.join(os.path.basename(f).split(' ')) \
            for f in glob.glob(m['repo'] + '*csv')]

    
    if first:
        driver.get(m['url'])

        elem = driver.find_element_by_name("email")
        elem.clear()
        elem.send_keys(cred['email'])

        elem = driver.find_element_by_name("pass")
        elem.clear()
        elem.send_keys(cred['pass'])

        elem.send_keys(Keys.RETURN)

        WebDriverWait(driver, 15).until(EC.url_changes(m['url']))

        driver.get(m['url2'])

        first = False

    #e = driver.find_element_by_xpath("/html/body/div[1]/div[2]/div/h1/a") 
    #driver.get(m['url2'])
    #driver.manage().timeouts().implicitlyWait(10, TimeUnit.SECONDS);
    
    e = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/h1/a")
    main_text=e.text
    ##main_text.replace('Id Facebook','Id  Facebook')
    print(main_text)
    #E = driver.find_elements_by_xpath("/html/body/div[1]/div[2]/ul/li")
    E = driver.find_elements_by_xpath("/html/body/div[1]/div/div[2]/ul/li")
    D = []
    try:
        for e in E:
            element_text = e.text
            file_name = main_text + '_' + element_text + '.csv'
            file_name_no_space = ''.join(file_name.split(' '))
            if file_name_no_space not in repo:
                print('Getting ' + element_text)

                if not args.dry_run:
                    driver.find_element_by_link_text(e.text).click()
                    D.append(element_text)
                    time.sleep(30)
    except Exception as e:
        print('ERROR:' + str(e))
        print('Stopping scrape')

    if not args.dry_run:
        for d in D:
            print(d)
            print(config['downloads'] + '*' + d + '.csv')
            g = glob.glob(config['downloads'] + '*' + d + '.csv')
            print(g)
            if len(g) == 1:
                print('Moving ' + g[0])
                new_loc = m['repo'] + '/' + os.path.basename(g[0])
                os.rename(g[0], new_loc)
            else:
                print('Move to repo failed. Multiple files ended in ' + d + '.csv')

