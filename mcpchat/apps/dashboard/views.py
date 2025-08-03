from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from apps.dashboard.models import Dashboard
import json
import ast
import plotly.express as px
import pandas as pd
# Create your views here.

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect(reverse("index:login"))
    
    dashboards = Dashboard.objects.filter(user=request.user)

    return render(request, 'dashboard/dashboard.html',{
        'dashboards': dashboards
    })

def dashboard_detalle(request, id):
    if not request.user.is_authenticated:
        return redirect(reverse("index:login"))
    
    panel = Dashboard.objects.get(id=id)
    print("**********DEBUG********")

    df = pd.DataFrame(panel.datos_json["datos"])

    # Crear gráficos Plotly
    barra_vertical = px.bar(df, x="categoria", y="valor", title="Gráfico de barras").to_html(full_html=False)
    torta = px.pie(df, names="categoria", values="valor",title="Gráfico de torta").to_html(full_html=False)
    anillo = px.pie(df, names="categoria", values="valor", hole=0.7, title="Gráfico de anillos").to_html(full_html=False)
    linea = px.line(df, x="categoria", y="valor", markers=True, title="Gráfico de líneas").to_html(full_html=False)
    barra_horizontal = px.bar(df, x="valor", y="categoria", orientation='h', title="Gráfico de barras horizontal").to_html(full_html=False)

    return render(request, 'dashboard/dashboard_detalle.html', {
        'barra_vertical': barra_vertical,
        'torta': torta,
        'anillo':anillo,
        'linea': linea,
        'barra_horizontal': barra_horizontal,
        'titulo':panel.datos_json["titulo"],
    })