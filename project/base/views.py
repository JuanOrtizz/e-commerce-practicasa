from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'base/index.html')

# View para FAQs
def faqs(request):
    return render(request, 'base/faqs.html')