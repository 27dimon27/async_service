import time
import requests
from concurrent import futures
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

executor = futures.ThreadPoolExecutor(max_workers=1)

def calculate_service_cost(service_data):
    service_id = service_data['software_service_id']
    price = service_data['price']
    page_count = service_data.get('page_count', 1)
    
    calculated_sum = price * page_count
    
    return {
        'software_service_id': service_id,
        'calculated_sum': calculated_sum,
        'page_count': page_count,
        'original_price': price
    }

def send_calculation_results(task):
    try:
        results = task.result()
    except futures._base.CancelledError:
        return
    
    bid_id = results[0]
    results = [{key:result[key] for key in ["software_service_id", "calculated_sum"]} for result in results[1:]]
    
    callback_data = {
        'bid_id': bid_id,
        'services': results,
        'auth_token': settings.AUTH_TOKEN
    }
    
    try:
        response = requests.post(
            f"{settings.GO_BACKEND_URL}/update-calculations",
            json=callback_data,
            timeout=10
        )
        print(f"Results sent to Go backend. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending results to Go backend: {e}")

@api_view(['POST'])
def calculate_bid_services(request):
    """
    Основной endpoint для расчета стоимости услуг в заявке
    Принимает: bid_id и список услуг
    """
    if 'bid_id' not in request.data or 'services' not in request.data:
        return Response(
            {'error': 'Missing bid_id or services'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    bid_id = request.data['bid_id']
    services_data = request.data['services']
    auth_token = request.data.get('auth_token')
    
    if auth_token != settings.AUTH_TOKEN:
        return Response(
            {'error': 'Invalid authentication token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    task = executor.submit(process_services_calculation, services_data, bid_id)
    task.add_done_callback(send_calculation_results)
    
    return Response({
        'message': 'Calculation process started. Results will be sent back shortly.'
    }, status=status.HTTP_200_OK)

def process_services_calculation(services_data, bid_id):
    time.sleep(10)
    results = [bid_id]
    for service in services_data:
        calculated_service = calculate_service_cost(service)
        results.append(calculated_service)
    
    return results

@api_view(['GET'])
def health_check(request):
    """
    Endpoint для проверки работоспособности сервиса
    """
    return Response({
        'status': 'healthy',
        'service': 'Async Calculation Service',
        'version': '1.0'
    })