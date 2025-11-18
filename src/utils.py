import streamlit as st
import plotly.express as px
import pandas as pd

plot_colors = ['#d3d3d3', '#767676', '#4f4f4f', '#6aff67','#ffffff']

def plot_pie(data, col_values, col_names):
    fig = px.pie(
                data,
                values=col_values,
                names=col_names,
                hole=0.5,
                facet_col_wrap=0,
                width=700,
                height=350,
                labels=None,
                color_discrete_sequence=plot_colors
            )

    fig.update_traces(textposition='inside', textinfo='value+label')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', showlegend=False)
                
    st.plotly_chart(fig, use_container_width=True)

def plot_bar(data, col_category, col_values):
    fig = px.bar(
        data, 
        x=col_category, 
        y=col_values, 
        title='Gráfico de Barras Simple con Plotly',
        labels={col_category: 'Clasificación', col_values: 'Magnitud'},
        color_discrete_sequence=['#d3d3d3', '#767676', '#4f4f4f', '#6aff67','#ffffff'],  # Opcional: para colorear por categoría
        color=col_category
    )

    # Opcional: Personalización adicional (e.g., actualizar el diseño)
    fig.update_layout(
        xaxis_title='Categoría de Datos',
        yaxis_title='Valor Correspondiente',
        font=dict(
            size=14,
            color="White"
        ),
        # Ajustar el ancho de las barras (0.8 es el valor por defecto)
        bargap=0,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)