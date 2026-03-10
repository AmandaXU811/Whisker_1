function demo1_plot_raw_data(app, ax)
    
    comport = readlines("COMdetails.txt");

    % Setup EIDORS (same as before)
    %addpath(genpath('C:\Users\imaan\Downloads\eidors-v3.12-ng\eidors'));
    %run('C:\Users\imaan\Downloads\eidors-v3.12-ng\eidors-v3.12-ng\eidors\startup.m');

    % Create model
    %imdl = mk_common_model('b2d1c', 16);
    %sim_img = mk_image(imdl.fwd_model, 1);
    %stim = mk_stim_patterns(16, 1, '{op}', '{ad}', {}, 1);
    %sim_img.fwd_model.stimulation = stim;

    % Reconstruction settings
    % imdl.hyperparameter.value = 0.1;
    % imdl.RtR_prior = 'prior_laplace';

    % Connect to board
    clear device
    device = serialport(comport, 115200);
    device.Timeout = 25;
    device.write("y", "string");

    % Read baseline frame
    data = readline(device); 
    plotthis = str2double(data);
    baseline = plotthis;

 
    accumulateddata = [];

    % Plot the first value to show something early
    plot(ax, baseline, 'b');
    title(ax, 'Live Raw Signal');
    drawnow;

    % Number of data frames to read
    n = 300;
    
    flush(device);
    for i = 1:n
        flush(device);
        data = readline(device);
        value = str2double(data);

        if ~isnan(value)
            accumulateddata = [accumulateddata; value];

            % Plot the accumulated data over time
            plot(ax, accumulateddata, 'b');
            xlim(ax, [max([1, i-50]) max([i 50])]);
            title(ax, sprintf('Frame %d', i));
            drawnow;
        end
    end

    clear device
end
