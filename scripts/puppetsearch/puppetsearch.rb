#!/usr/bin/ruby
require "puppet"
require "optparse"

# Note: This script requires puppet >= 0.25.5.

Puppet.settings.parse

options = {
  :node => Puppet[:certname],
  :types => [],
  :source => :yaml,
}

OptionParser.new do |opts|
  opts.banner = "Usage: puppetsearch [options] title1 title2 ..."

  opts.on("-n",
          "--node NODENAME",
          "Search on node NODENAME") do |node|
    options[:node] = node
  end

  opts.on("-t",
          "--types TYPES",
          "Comma-separated list of resource types to search for") do |types|
    options[:types] = types.split(",")
  end

  opts.on("-s",
          "--source SOURCE",
          "Catalog source (yaml, compiler, rest, etc.)") do |source|
    options[:source] = source
  end
end.parse!

# Search for files by default.
if options[:types].empty?
  options[:types] << "File"
end

Puppet[:catalog_terminus] = options[:source]

catalog = Puppet::Resource::Catalog.find(options[:node])

if catalog.nil?
    abort "Could not load catalog."
end

ARGV.each do |search_title|
  options[:types].each do |type|
    resource = catalog.resource(type, search_title)
    unless resource.nil?
      puts "#{resource} defined in #{resource.file}"
    end
  end
end

