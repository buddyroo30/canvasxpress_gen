use LLMCaller;

my $caller = LLMCaller->new(base_url => 'http://canvasxpress.org:5000');
$caller->set_params(
    config_only => 'True',
    model => 'gpt-4-32k',
    topp => 1,
    temperature => 0,
    presence_penalty => 0,
    frequency_penalty => 0,
    max_new_tokens => 1250,
    prompt => 'box plot of len on x axis grouped by dose',
    datafile_contents => '[["len","dose"]]'
);

my $result = $caller->get;  # or $caller->post;
print $result;