Puppet::Type.type(:network_config).provide(:interfaces) do
  desc "Provider for configuration of Ubuntu interfaces"
  defaultfor :operatingsystem => [ :ubuntu, :debian ]

  @@exclusive = nil
  @@configured_devices = []
  @@instance_count = 0
  @@total_resource_count = 0

  def initialize(args)
    @@main_config_file = "/etc/network/interfaces"
    @@config_dir = "/etc/network/interfaces.d/"
    super(args)
    @@configured_devices << "ifcfg-#{@resource[:device]}"
    @@total_resource_count += 1
    Dir.mkdir(@@config_dir.to_s) unless File.exists?(@@config_dir.to_s)
  end

  def exists?
    @@instance_count += 1
    @config_file = "#{@@config_dir}ifcfg-#{@resource[:device]}"

    # do not check file contents if the purpose is to ensure the file isn't there
    return File.exists?(@config_file) if @resource[:ensure] == :absent

    # load puppet configuration (`should`)
    @memory_values = {}

    # Get any property set in the resource that isn't a metaparameter
    mp = Puppet::Type::metaparams << :ensure << :provider << :exclusive
    @resource.to_hash.delete_if { |k,v| mp.include? k }.each_pair { |k, v|
      case k.to_s
        when /address/
          new_k = 'ipaddr'
          new_v = v.to_s
        when /iface/
          next
        when /auto/
          new_k = 'onboot'
          new_v = 'yes'
        else
          new_k = k.to_s
          new_v = v.to_s
      end
      @memory_values[new_k] = new_v unless v.nil?
    }

    # handle the special hack with :exclusive
    @@exclusive = @resource.to_hash[:exclusive] if @@exclusive.nil?

    # if this is the last file to be checked, trigger exclusivity enforcement
    enforce_exclusivity if (@@instance_count == @@total_resource_count)

    return @disk_values == @memory_values
  end

  def clear
    @@configured_devices = []
    @@instance_count = 0
    @@total_resource_count = 0
    @@exclusive = nil
  end

  def create
    #adaption rhel objects to ubuntu
    convert()
    File.open(@config_file.to_s, 'w') do |f|
      f.write("# Generated by puppet-network on #{Time.now.strftime("%F %T")}\n")
      if @memory_values['onboot']="true" then f.write("auto #{@resource[:device]}\n") end
      case @memory_values['bootproto']
        when /dhcp/
          if_str = "iface #{@resource[:device]} inet dhcp"
        when /static/
          if_str = "iface #{@resource[:device]} inet static"
        when /none/
          if_str = "iface #{@resource[:device]} inet manual"
      end
      if not @resource['name'] == 'lo' then f.write("#{if_str}\n")
      else f.write("iface #{@resource[:device]} inet loopback\n") end
      @converted_values.each_pair do |k, v|
        # only quote values that include space or equal characters
        quote_value = v.include?(' ') or v.include?('=')
        vs = v.nil? ? k : quote_value ? "#{k} \"#{v}\"" : "#{k} #{v}"
        f.write("#{vs}\n")
      end
      if @memory_values['vlan'] == 'yes' then f.write("vlan_raw_device #{@resource[:device].split(".")[0]}") end
    end
    system("grep -q \"source.*#{@resource[:device]}\" #{@@main_config_file} || echo \"source #{@config_file}\" >> #{@@main_config_file}")
    unless @@exclusive == :false 
       system("sed -i /source.*#{@resource[:device]}/!d #{@@main_config_file}")
    end
    system("ifdown #{@resource[:device]};sleep 2;ifup #{@resource[:device]}")
  end

  def destroy
    system("ifdown #{@resource[:device]}")
    system("sed -i /source.*#{@resource[:device]}/d #{@@main_config_file}")
    if File.exists?(@config_file)
      Puppet.notice "Destroying #{@config_file}"
      File.unlink(@config_file)
    end
  end

  def load_disk_config
    return nil unless File.exists?(@config_file)
    config_hash = {}

    File.readlines(@config_file).each do |line|
      next unless line =~ /^\s*([A-Za-z][^\s]+)\s"?([^"]+)"?$/
      config_hash[$1.strip.upcase.to_sym] = $2.strip
    end

    Puppet.debug "Loaded file: #{@config_file}"
    notice ("")
    return config_hash
  end

  def enforce_exclusivity
    unless @@exclusive == :false
      existing = Dir["#{@@config_dir}ifcfg-*"].map { |f| File.basename(f) }
      (existing - @@configured_devices).each do |parasite_file|
        intf = parasite_file.gsub(/^ifcfg-/,"")
        Puppet.notice "puppet-network exclusive: deleting interface #{intf} and removing #{parasite_file}"
        system("ifdown #{intf}")
        File.delete("#{@@config_dir}#{parasite_file}")
      end
      File.delete("#{@@main_config_file}")
      @@configured_devices.each do |intf_file|
        system("echo \"source #{@@config_dir}#{intf_file}\" >> #{@@main_config_file}")
      end
    end
    clear()
  end

  def convert
    @converted_values = {}
    @memory_values.each_pair do |k, v|
      case k.to_s
        when /ipaddr/
          k="address"
        when /bootproto/,/onboot/,/nozeroconf/,/domain/,/delay/,/device/,/userctl/,/vlan/
          next
        end
      @converted_values[k.to_s] = v.to_s
    end
  end

end
