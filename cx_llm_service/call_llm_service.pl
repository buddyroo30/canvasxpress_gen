sub ask {

  my $p = [ split( /,/, $config ) ];

  $llm->set_params( 
    config_only => 'True',
    model => $p->[0],
    topp => $p->[1],
    temperature => $p->[2],
    presence_penalty => $p->[3],
    frequency_penalty => $p->[4],
    max_new_tokens => $p->[5],
    prompt => $prompt,
    datafile_contents => $header
  );

  my $res = decode_json($llm->get());

  $res->{target} = $target;
  $res->{client} = $client;

  $cgi->printHeader('json');
  $cgi->printContent("CanvasXpress.callbackLLM(" . encode_json($res) . ")");

}

#Called from Javascript like this:
#this.askLLM = function (t) {
#    return function (e) {
#      var i = t.$(t.target + '-cX-ChatInterfaceAsk');
#      var m = CanvasXpress.doc.P.llmModel.O;
#      if (i && i.value != '') {
#        // Validate the parameters
#        if (!m.includes(t.llmModel)) {
#          t.llmModel = m[0];
#        }
#        t.llmTopp = Math.max(0, Math.min(1, t.llmTopp));
#        t.llmTemperature = Math.max(0, Math.min(2, t.llmTemperature));
#        t.llmPresencePenalty = Math.max(-2, Math.min(2, t.llmPresencePenalty));
#        t.llmFrequencyPenalty = Math.max(-2, Math.min(2, t.llmFrequencyPenalty));
#        t.llmMaxNewTokens = Math.max(1250, Math.min(2048, t.llmMaxNewTokens));
#        var h = t.stringifyJSON(t.cXHeaderToArray());
#        var x = CanvasXpress.factory.client;
#        var c = [t.llmModel, t.llmTopp, t.llmTemperature, t.llmPresencePenalty, t.llmFrequencyPenalty, t.llmMaxNewTokens].join(',');
#        // Ask the LLM
#        var src = t.llmServiceURL + "?service=ask&target=" + t.target + "&client=" + x + "&config=" + c + "&prompt=" + i.value + "&header=" + h;
#        var s = document.createElement("script");
#        s.src = encodeURI(src);
#        document.body.appendChild(s);
#      }
#    }
#  }(this);