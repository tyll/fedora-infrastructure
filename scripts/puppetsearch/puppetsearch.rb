#!/usr/bin/ruby
require "yaml"
require "puppet"
require "optparse"

def find_resource(catalog, type, query_file)
  resource = catalog.resource(type, query_file)
  unless resource.nil?
    resource.file
  end
end

options = {
  :types => [],
}

OptionParser.new do |opts|
  opts.banner = "Usage: puppetsearch [options] title1 title2 ..."

  opts.on("-y",
          "--yamlfile YAMLFILE",
          "Read catalog from YAMLFILE") do |yamlfile|
    options[:yamlfile] = yamlfile
  end

  opts.on("-t",
          "--types TYPES",
          "Comma-separated list of resource types to search for") do |types|
    options[:types] = types.split(',')
  end
end.parse!

# Search for files by default.
if options[:types].empty?
  options[:types] << "File"
end

if options[:yamlfile].nil?
  require "facter"

  fqdn = Facter.value(:fqdn)
  if fqdn.nil?
    abort "Error: Could not determine FQDN"
  end

  client_yaml = Puppet[:clientyamldir]
  if client_yaml.nil?
      abort "Could not determine client YAML directory."
  end

  options[:yamlfile] = "#{client_yaml}/catalog/#{fqdn}.yaml"
end

catalog = YAML::load_file(options[:yamlfile])

ARGV.each do |search|
  options[:types].each do |type|
    manifest = find_resource(catalog, type, search)
    puts "#{type}[#{search}] defined in #{manifest}"
  end
end

