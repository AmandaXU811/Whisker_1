function data_row = demo_4_theQuartiles(plot_ax)
    
    %addpath(genpath('C:\Users\imaan\Downloads\eidors-v3.12-ng\eidors'));
    %evalc("run('C:\Users\imaan\Downloads\eidors-v3.12-ng\eidors-v3.12-ng\eidors\startup.m');")

    % Create model
    %imdl = mk_common_model('b2d1c', 16);
    %sim_img = mk_image(imdl.fwd_model, 1);
    %stim = mk_stim_patterns(16, 1, '{op}', '{ad}', {}, 1);
    %sim_img.fwd_model.stimulation = stim;
    %imdl.hyperparameter.value = 0.1;
    %imdl.RtR_prior = 'prior_laplace';

    % Connect to Teensy
    comport = readlines("COMdetails.txt");
    device = serialport(comport, 115200);
    device.Timeout = 25;
    device.write("y", "string");

    % Baseline frame
    baseline = readline(device);

    % Read one frame
    raw = readline(device);
    data_row = str2num(raw);
    data_row = data_row(data_row ~= 0);  % remove zeros

    if nargin > 0 && isvalid(plot_ax)
        plot(plot_ax, data_row, 'LineWidth', 1.5);
        title(plot_ax, 'Raw Data from Trial');
        xlabel(plot_ax, 'Channel Index');
    end

 
    clear device;
end
