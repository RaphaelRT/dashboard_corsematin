import dash
import dash_html_components as html
from dash.dependencies import Output, Input, State
from utils_func import Utils
from dash_app import app

utils = Utils()
initial_datas = utils.get_initial_datas()
reco = initial_datas[2]
def generate_message(reco_stats, value, column_name, outputs, messages):
    max_val = int(reco_stats[column_name].values[0] * 1.1)
    min_val = int(reco_stats[column_name].values[0] * 0.9)
    color_wrong = "#e74c3c"
    color_good = "#2ecc71"
    messages = [m + f" \n (Reco : {min_val} - {max_val})" for m in messages]
    #print(min_val, max_val)
    if value > max_val:
            #print(value, max_val)
            outputs.append(html.Span(className='output-span', children=messages[0], style={"color": color_wrong}))
    if value < min_val:
            #print(value, min_val)
            outputs.append(html.Span(className='output-span', children=messages[1], style={"color": color_wrong}))
    if value in range(min_val, max_val+1):
            outputs.append(html.Span(className='output-span', children=messages[2], style={"color": color_good}))
            #print(messages[2])
    return outputs
def reco_callbacks(cache, TIMEOUT, region, df):
  
  @app.callback(
      [
          Output("reco_container", "children"),
          Output("info_content", "children")
      ],
      [
          Input('url', 'pathname'),
          Input('submit_button', 'n_clicks'),
          State("section_name_dropdown", "value"),
          State("input_area", "value"),
          State("title_input_area", "value")
      ],
  )
  def update_charts(pathname,  n_clicks, section_name_dropdown, input_area, title_input_area):
    
    info_input = []
    reco_stats = reco[reco["section_name"] == section_name_dropdown]
    if title_input_area:
        word_count_title_input = utils.get_word_count(title_input_area.strip())
        char_count_title_input = utils.get_char_count(title_input_area.strip())
    if input_area:
        word_count_input = utils.get_word_count(input_area.strip())
        char_count_input = utils.get_char_count(input_area.strip())
        sentence_count_input = utils.get_sentence_count(input_area.strip())
        sentence_len_count_input = int(word_count_input / sentence_count_input)
    if input_area is None or input_area == "" or input_area == " ":
        word_count_input = 0
        char_count_input = 0
        sentence_count_input = 0
        sentence_len_count_input = 0
    info_input.append(html.Span(className='output-span', children=f"Nombre de mot = {word_count_input}"))
    #info_input.append(html.Span(className='output-span', children=f"Nombre de caractères = {char_count_input}"))
    info_input.append(html.Span(className='output-span', children=f"Nombre de phrase = {sentence_count_input}"))
    info_input.append(html.Span(className='output-span', children=f"Longueur de phrase moyenne = {sentence_len_count_input} mot(s)"))
    if n_clicks > 0:
        outputs = []
        if char_count_input > 1 and input_area:
            outputs = generate_message(
                reco_stats,
                word_count_title_input,
                "word_count_title",
                outputs,
                ["❌ Le titre a trop de mots !", "❌ Le titre n'a pas assez de mots", "✅ Le titre a le bon nombre de mots"]
            )
            #outputs = generate_message(
                #reco_stats,
                #char_count_title_input,
                #"char_count_title",
                #outputs,
                #["❌ Le titre a trop de caractères !", "❌ Le titre a pas assez de caractères", "✅ Le titre a le bon nombre de caractères"]
            #)
            outputs = generate_message(
                reco_stats,
                word_count_input,
                "word_count",
                outputs,
                ["❌ L'article a trop de mots !", "❌ L'article n'a pas assez de mots", "✅ L'article a le bon nombre de mots"]
            )
            outputs = generate_message(
                reco_stats,
                char_count_input,
                "char_count",
                outputs,
                ["❌ L'article a trop de caractères !", "❌ L'article a pas assez de caractères", "✅ L'article a le bon nombre de caractères"]
            )
            outputs = generate_message(
                reco_stats,
                sentence_count_input,
                "sentence_count",
                outputs,
                ["❌ L'article a trop de phrases !", "❌ L'article a pas assez de phrases", "✅ L'article a le bon nombre de phrases"]
            )
            outputs = generate_message(
                reco_stats,
                sentence_len_count_input,
                "avg_sentence_lenght",
                outputs,
                ["❌ L'article a des phrases trop longue !", "❌ L'article a des phrases trop courtes !", "✅ L'article a des phrases de bonne longueur"]
            )

            
            #print(outputs)
            return [html.Div(children=outputs)], [html.Div(children=info_input)]
        print(pathname)
        print(section_name_dropdown)    
        print(input_area)
        print(outputs)

    return [html.Span(className='output-span', children='Veuillez entrer votre article !')], [html.Div(children=info_input)]