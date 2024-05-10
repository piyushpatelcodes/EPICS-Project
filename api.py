import requests
from bs4 import BeautifulSoup

def get_vehicle_details(first, second):
    # URL and form data
    url = 'https://parivahan.gov.in/rcdlstatus/'
    data = {
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'form_rcdl:j_idt32',
        'javax.faces.partial.execute': '@all',
        'javax.faces.partial.render': 'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl',
        'form_rcdl:j_idt32': 'form_rcdl:j_idt32',
        'form_rcdl': 'form_rcdl',
        'form_rcdl:tf_reg_no1': first,
        'form_rcdl:tf_reg_no2': second
    }

    # Make the initial POST request
    response = requests.post(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract ViewState token
    token = soup.find('input', {'name': 'javax.faces.ViewState'})['value']
    cookies = response.headers['Set-Cookie']

    # Add ViewState token to data
    data['javax.faces.ViewState'] = token

    # Make the second POST request with updated data and cookies
    headers = {'Cookie': cookies}
    response2 = requests.post(url, data=data, headers=headers)
    soup2 = BeautifulSoup(response2.text, 'html.parser')

    # Parse the vehicle details from the response
    details = {}
    for td in soup2.find_all('table')[0].find_all('td'):
        if td.find('span', {'class': 'font-bold'}):
            key = td.find('span', {'class': 'font-bold'}).text.strip()
            value = td.find('span', {'class': 'font-bold'}).find_next('td').text.strip()
            details[key] = value

    return details

# Example usage
if __name__ == "__main__":
    first = input("Enter first part of vehicle registration number: ")
    second = input("Enter second part of vehicle registration number: ")
    vehicle_details = get_vehicle_details(first, second)
    print(vehicle_details)
