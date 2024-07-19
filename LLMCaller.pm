package LLMCaller;

use strict;
use warnings;
use LWP::UserAgent;
use HTTP::Request::Common qw(GET POST);
use URI::Escape;

sub new {
    my ($class, %args) = @_;
    my $self = bless {}, $class;
    $self->{base_url} = $args{base_url};
    $self->{ua} = LWP::UserAgent->new;
    return $self;
}

sub set_params {
    my ($self, %params) = @_;
    $self->{params} = \%params;
}

sub get {
    my $self = shift;
    my $url = $self->{base_url} . '/ask?' . $self->_build_query_string;
    my $response = $self->{ua}->request(GET $url);
    return $response->is_success ? $response->decoded_content : undef;
}

sub post {
    my $self = shift;
    my $url = $self->{base_url} . '/ask';
    my $response = $self->{ua}->request(POST $url, Content => $self->_build_query_string);
    return $response->is_success ? $response->decoded_content : undef;
}

sub _build_query_string {
    my $self = shift;
    return join '&', map { uri_escape($_) . '=' . uri_escape($self->{params}{$_}) } keys %{$self->{params}};
}

1;