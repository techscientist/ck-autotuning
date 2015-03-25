#
# Collective Knowledge (program)
#
# See CK LICENSE.txt for licensing details
# See CK Copyright.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://cTuning.org/lab/people/gfursin
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings
sep='***************************************************************************************'

##############################################################################
# Initialize module

def init(i):
    """

    Input:  {}

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# compile program

def process(i):
    """
    Input:  {
              sub_action   - clean, compile, run

              (repo_uoa)   - program repo UOA
              (module_uoa) - program module UOA
              data_uoa     - program data UOA

              (process_in_tmp)       - (default 'yes') - if 'yes', clean, compile and run in the tmp directory 
              (tmp_dir)              - (default 'tmp') - if !='', use this tmp directory to clean, compile and run
              (generate_rnd_tmp_dir) - if 'yes', generate random tmp directory            
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              Output of the last compile from function 'process_in_dir'

              tmp_dir      - directory where clean, compile, run
            }

    """

    import os
    import copy

    ic=copy.deepcopy(i)

    # Check if global writing is allowed
    r=ck.check_writing({})
    if r['return']>0: return r

    o=i.get('out','')

    a=i.get('repo_uoa','')
    m=i.get('module_uoa','')
    duoa=i.get('data_uoa','')

    lst=[]

    if duoa=='':
       # First, try to detect CID in current directory
       r=ck.cid({})
       if r['return']==0:
          a=r.get('repo_uoa','')
          m=r.get('module_uoa','')
          duoa=r.get('data_uoa','')

       if duoa=='':
          # Attempt to load configuration from the current directory
          p=os.getcwd()

          pc=os.path.join(p, ck.cfg['subdir_ck_ext'], ck.cfg['file_meta'])
          if os.path.isfile(pc):
             r=ck.load_json_file({'json_file':pc})
             if r['return']==0:
                d=r['dict']

                ii=copy.deepcopy(ic)
                ii['path']=p
                ii['meta']=d
                return process_in_dir(ii)

          return {'return':1, 'error':'data UOA is not defined'}

    # Check wildcards
    if a.find('*')>=0 or a.find('?')>=0 or m.find('*')>=0 or m.find('?')>=0 or duoa.find('*')>=0 or duoa.find('?')>=0: 
       r=ck.list_data({'repo_uoa':a, 'module_uoa':m, 'data_uoa':duoa})
       if r['return']>0: return r

       lst=r['lst']
    else:
       # Find path to data
       r=ck.find_path_to_data({'repo_uoa':a, 'module_uoa':m, 'data_uoa':duoa})
       if r['return']>0: return r
       p=r['path']
       ruoa=r.get('repo_uoa','')
       ruid=r.get('repo_uid','')
       muoa=r.get('module_uoa','')
       muid=r.get('module_uid','')
       duid=r.get('data_uid','')
       duoa=r.get('data_alias','')
       if duoa=='': duoa=duid

       lst.append({'path':p, 'repo_uoa':ruoa, 'repo_uid':ruid, 
                             'module_uoa':muoa, 'module_uid':muid, 
                             'data_uoa':duoa, 'data_uid': duid})

    r={'return':0}
    for ll in lst:
        p=ll['path']

        ruid=ll['repo_uid']
        muid=ll['module_uid']
        duid=ll['data_uid']

        r=ck.access({'action':'load',
                     'repo_uoa':ruid,
                     'module_uoa':muid,
                     'data_uoa':duid})
        if r['return']>0: return r

        d=r['dict']

        if o=='con':
           ck.out('')

        ii=copy.deepcopy(ic)
        ii['path']=p
        ii['meta']=d
        ii['repo_uoa']=ruid
        ii['module_uoa']=muid
        ii['data_uoa']=duid
        r=process_in_dir(ii)
        if r['return']>0: return r

    return r      

##############################################################################
# compile program  (called from universal function here)

def process_in_dir(i):
    """
    Input:  {
              Comes from 'compile', 'run' and 'clean' functions

              sub_action             - clean, compile, run

              path                   - path
              meta                   - program description

              (generate_rnd_tmp_dir) - if 'yes', generate random tmp directory to compile and run program
                                       (useful during crowd-tuning)

              (flags)                - compile flags
              (lflags)               - link flags

              (compile_type)         - static or dynamic (dynamic by default)
                  or
              (static or dynamic)

              (repeat)               - repeat kernel via environment CT_REPEAT_MAIN if supported

              (clean)                - if 'yes', clean tmp directory before using
              (skip_clean_after)     - if 'yes', do not remove run batch

              (repo_uoa)             - program repo UOA
              (module_uoa)           - program module UOA
              (data_uoa)             - program data UOA

              (misc)                 - misc  dict
              (characteristics)      - characteristics/features/properties
              (env)                  - preset environment

              (deps)                 - already resolved deps (useful for auto-tuning)

              (skip_device_init)     - if 'yes', do not initialize device

              (skip_calibration)     - if 'yes', skip execution time calibration (make it around 4.0 sec)
              (calibration_time)     - calibration time in string, 4.0 sec. by default
              (calibration_max)      - max number of iterations for calibration, 10 by default
            }

    Output: {
              return          - return code =  0, if successful
                                            >  0, if error
              (error)         - error text if return > 0

              misc            - updated misc dict
              characteristics - updated characteristics
              env             - updated environment
              deps            - resolved deps, if any
            }

    """
    import os
    import time
    import sys
    import shutil

    start_time=time.time()

    sys.stdout.flush()

    o=i.get('out','')

    misc=i.get('misc',{})
    ccc=i.get('characteristics',{})
    env=i.get('env',{})
    deps=i.get('deps',{})

    flags=i.get('flags','')
    lflags=i.get('lflags','')
    repeat=int(i.get('repeat','-1'))

    ctype=i.get('compile_type','')
    if ctype=='': ctype='dynamic'

    if i.get('static','')=='yes': ctype='static'
    if i.get('dynamic','')=='yes': ctype='dynamic'

    # Check host/target OS/CPU
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    tdid=i.get('target_device_id','')

    r=ck.access({'action':'detect',
                 'module_uoa':cfg['module_deps']['platform.os'],
                 'host_os':hos,
                 'target_os':tos,
                 'target_device_id':tdid,
                 'skip_info_collection':'yes'})
    if r['return']>0: return r

    hos=r['host_os_uid']
    hosx=r['host_os_uoa']
    hosd=r['host_os_dict']

    tos=r['os_uid']
    tosx=r['os_uoa']
    tosd=r['os_dict']

    remote=tosd.get('remote','')

    tbits=tosd.get('bits','')

    # update misc
    misc['host_os_uoa']=hosx
    misc['target_os_uoa']=tosx
    misc['target_device_id']=tdid

    # Get host platform type (linux or win)
    rx=ck.get_os_ck({})
    if rx['return']>0: return rx
    hplat=rx['platform']

    rem=hosd.get('rem','')
    eset=hosd.get('env_set','')
    etset=tosd.get('env_set','')
    svarb=hosd.get('env_var_start','')
    svarb1=hosd.get('env_var_extra1','')
    svare=hosd.get('env_var_stop','')
    svare1=hosd.get('env_var_extra2','')
    scall=hosd.get('env_call','')
    sdirs=hosd.get('dir_sep','')
    stdirs=tosd.get('dir_sep','')
    sext=hosd.get('script_ext','')
    sexe=hosd.get('set_executable','')
    se=tosd.get('file_extensions',{}).get('exe','')
    sbp=hosd.get('bin_prefix','')
    stbp=tosd.get('bin_prefix','')
    sqie=hosd.get('quit_if_error','')
    evs=hosd.get('env_var_separator','')
    envsep=hosd.get('env_separator','')
    envtsep=tosd.get('env_separator','')
    eifs=hosd.get('env_quotes_if_space','')
    eifsc=hosd.get('env_quotes_if_space_in_call','')
    wb=tosd.get('windows_base','')
    stro=tosd.get('redirect_stdout','')
    stre=tosd.get('redirect_stderr','')

    ########################################################################
    # Prepare some params
    misc=i.get('misc',{})
    misc.update({'host_os_uoa':hos,
                 'target_os_uoa':tos,
                 'target_os_bits':tbits})

    # Get host platform
    rx=ck.get_os_ck({})
    if rx['return']>0: return rx
    ios=rx['platform']

    p=i['path']
    meta=i['meta']

    ruoa=i.get('repo_uoa', '')
    muoa=i.get('module_uoa', '')
    duoa=i.get('data_uoa', '')

    target_exe=meta.get('target_file','')
    if target_exe=='':
       target_exe=cfg.get('target_file','')
    if meta.get('skip_bin_ext','')!='yes':
       target_exe+=se

    # If muoa=='' assume program
    if muoa=='':
       muoa=work['self_module_uid']

    if duoa=='':
       x=meta.get('backup_data_uid','')
       if x!='':
          duoa=meta['backup_data_uid']

    # Check if compile in tmp dir
    cdir=p
    os.chdir(cdir)

    sa=i['sub_action']

    ################################### Run ######################################
    if sa=='clean':
       # Get host platform type (linux or win)
       cmd=cfg.get('clean_cmds',{}).get(hplat)

       if o=='con':
          ck.out(cmd)
          ck.out('')

       rx=os.system(cmd)

       # Removing tmp directories
       curdir=os.getcwd()
       for q in os.listdir(curdir):
           if not os.path.isfile(q) and q.startswith('tmp'):
              shutil.rmtree(q, ignore_errors=True)

       return {'return':0}

    # Check tmp dir ...
    x=i.get('process_in_tmp','').lower()
    if x=='': x='yes'

    if x!='yes':
       x=meta.get('process_in_tmp','').lower()

    td=''
    if x=='yes':
       tdx=i.get('tmp_dir','')
       td=tdx
       if td=='': td='tmp'

       if i.get('clean','')=='yes':
          if td!='' and os.path.isdir(td):
             shutil.rmtree(td, ignore_errors=True)

       if tdx=='' and i.get('generate_rnd_tmp_dir','')=='yes':
          # Generate tmp dir
          import tempfile
          fd, fn=tempfile.mkstemp(suffix='', prefix='tmp-ck-')
          os.close(fd)
          os.remove(fn)
          td=os.path.basename(fn)

       cdir=os.path.join(p, td)

    misc['tmp_dir']=td
    misc['path']=p

    if cdir!='' and not os.path.isdir(cdir):
       os.mkdir(cdir)

    sb='' # Batch

    if o=='con':
       ck.out(sep)
       ck.out('Current directory: '+cdir)
       ck.out('')

    os.chdir(cdir)
    rcdir=os.getcwd()

    # If run and dynamic, check deps prepared by compiler
    fdeps=cfg.get('deps_file','')
    if len(deps)==0 and ctype=='dynamic' and sa=='run':
       if os.path.isfile(fdeps):
          ck.out('')
          ck.out('Reloading depedencies from compilation '+fdeps+' ...')

          rx=ck.load_json_file({'json_file':fdeps})
          if rx['return']>0: return rx
          deps=rx['dict']

    # If compile type is dynamic, reuse deps even for run (to find specific DLLs) 
    # (REMOTE PLATFORMS ARE NOT SUPPORTED AT THE MOMENT, USE STATIC COMPILATION)
    if (ctype=='dynamic' or sa=='compile'):
       # Resolve deps (if not ignored, such as when installing local version with all dependencies set)
       if len(deps)==0: 
          deps=meta.get('compile_deps',{})

       if len(deps)>0:
          if o=='con':
             ck.out(sep)

          ii={'action':'resolve',
              'module_uoa':cfg['module_deps']['env'],
              'host_os':hos,
              'target_os':tos,
              'target_device_id':tdid,
              'deps':deps,
              'add_customize':'yes'}
          if o=='con': ii['out']='con'

          rx=ck.access(ii)
          if rx['return']>0: return rx

          if sa=='compile' or remote!='yes':
             sb+=rx['bat']

          deps=rx['deps'] # Update deps (add UOA)

       if sa=='compile':
          rx=ck.save_json_to_file({'json_file':fdeps, 'dict':deps})
          if rx['return']>0: return rx

    # If compiler, load env
    comp=deps.get('compiler',{})
    comp_uoa=comp.get('uoa','')
    dcomp={}

    if comp_uoa!='':
       rx=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['env'],
                     'data_uoa':comp_uoa})
       if rx['return']>0: return rx
       dcomp=rx['dict']

    # Check sub_actions
    ################################### Compile ######################################
    if sa=='compile':
       # Clean target file
       if target_exe!='' and os.path.isfile(target_exe):
          os.remove(target_exe)

       # Add env
       for k in sorted(env):
           v=env[k]

           if eifs!='' and wb!='yes':
              if v.find(' ')>=0 and not v.startswith(eifs):
                 v=eifs+v+eifs

           sb+=eset+' '+k+'='+v+'\n'
       sb+='\n'

       # Check linking libs + include paths for deps
       sll=''
       sin=''
       for k in deps:
           kv=deps[k].get('cus',{})

           pl1=kv.get('path_lib','')
           pl2=kv.get('static_lib','')
           if pl2!='':
              if sll!='': sll+=' '
              sll+=eifsc
              if pl1!='': 
                 sll+=pl1+sdirs
              sll+=pl2+eifsc

           pl3=kv.get('path_include','')
           if pl3!='':
              if sin!='': sin+=' '
              sin+=svarb+'CK_FLAG_PREFIX_INCLUDE'+svare+eifsc+pl3+eifsc

       # Obtaining compile CMD (first from program entry, then default from this module)
       ccmds=meta.get('compile_cmds',{})
       ccmd=ccmds.get(hplat,{})
       if len(ccmd)==0:
          ccmd=ccmds.get('default',{})
       if len(ccmd)==0:
          ccmds=cfg.get('compile_cmds',{})
          ccmd=ccmds.get(hplat,{})
          if len(ccmd)==0:
             ccmd=ccmds.get('default',{})

       sccmd=ccmd.get('cmd','')
       if sccmd=='':
          return {'return':1, 'error':'compile CMD is not found'}

       # Source files
       sfs=meta.get('source_files',[])

       compiler_env=meta.get('compiler_env','')
       if compiler_env=='': compiler_env='CK_CC'

       sfprefix='..'+sdirs

       scfb=svarb+'CK_FLAGS_CREATE_OBJ'+svare
       scfb+=' '+svarb+'CK_COMPILER_FLAGS_OBLIGATORY'+svare
       if ctype=='dynamic':
          scfb+=' '+svarb+'CK_FLAGS_DYNAMIC_BIN'+svare
       elif ctype=='static':
          scfb+=' '+svarb+'CK_FLAGS_STATIC_BIN'+svare
       scfb+=' '+svarb+'CK_FLAG_PREFIX_INCLUDE'+svare+sfprefix

       scfa=''

       # Check build -D flags
       sbcv=''
       bcv=meta.get('build_compiler_vars',{})
       for k in bcv:
           kv=bcv[k]
           if sbcv!='': sbcv+=' '
           sbcv+=svarb+svarb1+'CK_FLAG_PREFIX_VAR'+svare1+svare+k
           if kv!='': sbcv+='='+kv

       # Prepare compilation
       sb+='\n'

       denv=dcomp.get('env',{})
       sobje=denv.get('CK_OBJ_EXT','')
       sofs=''
       xsofs=[]

       for sf in sfs:
           xcfb=scfb
           xcfa=scfa

           sf0,sf1=os.path.splitext(sf)

           sfobj=sf0+sobje
           if sofs!='': sofs+=' '
           sofs+=sfobj
           xsofs.append(sfobj)

           if sbcv!='': xcfb+=' '+sbcv

           if sin!='': xcfb+=' '+sin

           xcfb+=' '+flags

           if 'CK_FLAGS_OUTPUT' in denv:
              xcfa+=' '+svarb+'CK_FLAGS_OUTPUT'+svare+sfobj

           cc=sccmd
           cc=cc.replace('$#source_file#$', sfprefix+sf)

           cc=cc.replace('$#compiler#$', svarb+compiler_env+svare)

           cc=cc.replace('$#flags_before#$', xcfb)
           cc=cc.replace('$#flags_after#$', xcfa)

           sb+='echo '+eifs+cc+eifs+'\n'
           sb+=cc+'\n'
           sb+=sqie+'\n'

           sb+='\n'

       # Obtaining link CMD (first from program entry, then default from this module)
       if sofs!='':
          linker_env=meta.get('linker_env','')
          if linker_env=='': linker_env=compiler_env

          lcmds=meta.get('link_cmds',{})
          lcmd=lcmds.get(hplat,{})
          if len(lcmd)==0:
             lcmd=lcmds.get('default',{})
          if len(lcmd)==0:
             lcmds=cfg.get('link_cmds',{})
             lcmd=lcmds.get(hplat,{})
             if len(lcmd)==0:
                lcmd=lcmds.get('default',{})

          slcmd=lcmd.get('cmd','')
          if slcmd!='':
             slfb=svarb+'CK_COMPILER_FLAGS_OBLIGATORY'+svare
             slfb+=' '+lflags
             if ctype=='dynamic':
                slfb+=' '+svarb+'CK_FLAGS_DYNAMIC_BIN'+svare
             elif ctype=='static':
                slfb+=' '+svarb+'CK_FLAGS_STATIC_BIN'+svare

             slfa=' '+svarb+svarb1+'CK_FLAGS_OUTPUT'+svare1+svare+target_exe
             slfa+=' '+svarb+'CK_LD_FLAGS_MISC'+svare
             slfa+=' '+svarb+'CK_LD_FLAGS_EXTRA'+svare

             evr=meta.get('extra_ld_vars','')
             if evr!='':
                evr=evr.replace('$<<',svarb).replace('>>$',svare)
                slfa+=' '+evr

             if sll!='': slfa+=' '+sll

             cc=slcmd
             cc=cc.replace('$#linker#$', svarb+linker_env+svare)
             cc=cc.replace('$#obj_files#$', sofs)
             cc=cc.replace('$#flags_before#$', slfb)
             cc=cc.replace('$#flags_after#$', slfa)

             sb+='echo '+eifs+cc+eifs+'\n'
             sb+=cc+'\n'
             sb+=sqie+'\n'

       # Record to tmp batch and run
       rx=ck.gen_tmp_file({'prefix':'tmp-', 'suffix':sext, 'remove_dir':'yes'})
       if rx['return']>0: return rx
       fn=rx['file_name']

       rx=ck.save_text_file({'text_file':fn, 'string':sb})
       if rx['return']>0: return rx

       y=''
       if sexe!='':
          y+=sexe+' '+sbp+fn+envsep
       y+=' '+scall+' '+sbp+fn

       sys.stdout.flush()
       start_time1=time.time()

       rx=os.system(y)
       comp_time=time.time()-start_time1

       ccc['compilation_time']=comp_time

       if i.get('skip_clean_after','')!='yes':
          if fn!='' and os.path.isfile(fn): os.remove(fn)

       ofs=0
       if rx>0:
          misc['compilation_success']='no'
       else:
          misc['compilation_success']='yes'

          # Check some characteristics
          if os.path.isfile(target_exe):
             ccc['binary_size']=os.path.getsize(target_exe)

          # Check obj file sizes
          if len(xsofs)>0:
             ccc['obj_sizes']={}
             for q in xsofs:
                 if os.path.isfile(q):
                    ofs1=os.path.getsize(q)
                    ccc['obj_sizes'][q]=ofs1
                    ofs+=ofs1
             ccc['obj_size']=ofs

       ccc['compilation_time_with_module']=time.time()-start_time

       if o=='con':
          ck.out('')
          ck.out('Compilation time: '+('%.3f'%comp_time)+' sec.; Object size: '+str(ofs))

    ################################### Run ######################################
    elif sa=='run':
       start_time=time.time()

       sc=i.get('skip_calibration','')
       xcalibrate_time=i.get('calibration_time','')
       if xcalibrate_time=='': xcalibrate_time=cfg['calibration_time']
       calibrate_time=float(xcalibrate_time)

       # Update environment
       env1=meta.get('run_vars',{})
       for q in env1:
           if q not in env:
              env[q]=env1[q]

       # Update env if repeat
       if sc!='yes':
          if repeat!=-1:
             if 'CT_REPEAT_MAIN' not in env1:
                return {'return':1, 'error':'this program is not supporting execution time calibration'}
             env['CT_REPEAT_MAIN']=str(repeat) # it is fixed by user
             sc='yes'
          else:
             repeat=int(env1.get('CT_REPEAT_MAIN','1'))
             env['CT_REPEAT_MAIN']='$#repeat#$' # find later

       # Add env
       for k in sorted(env):
           v=env[k]

           if eifs!='' and wb!='yes':
              if v.find(' ')>=0 and not v.startswith(eifs):
                 v=eifs+v+eifs

           sb+=etset+' '+k+'='+v+'\n'
       sb+='\n'

       # Check cmd key
       run_cmds=meta.get('run_cmds',{})
       if len(run_cmds)==0:
          return {'return':1, 'error':'no CMD for run'}

       krun_cmds=sorted(list(run_cmds.keys()))

       kcmd=i.get('cmd_key','')
       if kcmd=='':
          if 'default' in krun_cmds: kcmd='default'
          else: 
             kcmd=krun_cmds[0]








       else:
          if kcmd not in krun_cmds:
             return {'return':1, 'error':'CMD key not found in program description'}

       # Command line key is set
       vcmd=run_cmds[kcmd]
       misc['cmd_keys']=kcmd

       c=''

       rt=vcmd.get('run_time',{})

       # Command line preparation
       c=rt.get('run_cmd_main','')
       if c=='':
          return {'return':1, 'error':'cmd is not defined'}

       # Remote dir
       if remote=='yes':
          rdir=tosd.get('remote_dir','')
          if rdir!='' and not rdir.endswith(stdirs): rdir+=stdirs

       # Replace bin file
       c=c.replace('$#BIN_FILE#$', stbp+target_exe)
       c=c.replace('$#os_dir_separator#$', stdirs)
       if remote=='yes':
          c=c.replace('$#src_path#$', rdir+stdirs)
       else:
          c=c.replace('$#src_path#$', p+sdirs)

       c=c.replace('$#env1#$',svarb)
       c=c.replace('$#env2#$',svare)

       sdi=i.get('skip_device_init','')

       # Check if takes datasets from CK
       dtags=vcmd.get('dataset_tags',[])
       dduoa=i.get('dataset_uoa','')
       if dduoa!='' or len(dtags)>0:
          if dduoa=='':
             misc['dataset_tags']=dtags

             tags=''
             for q in dtags:
                 if tags!='': tags+=','
                 tags+=q

             dmuoa=cfg['module_deps']['dataset']
             dduoa=i.get('dataset_uoa','')
             if dduoa=='':
                rx=ck.access({'action':'search',
                              'module_uoa':dmuoa,
                              'tags':tags})
                if rx['return']>0: return rx

                lst=rx['lst']

                if len(lst)==0:
                   return {'return':1, 'error':'no related datasets found (tags='+tags+')'}  
                elif len(lst)==1:
                   dduoa=lst[0].get('data_uid','')
                else:
                   dduoa=lst[0].get('data_uid','')














          if dduoa=='':
             return {'return':1, 'error':'dataset is not specified'}  




       # If remote
       if remote=='yes':
          if target_exe=='':
             return {'return':1, 'error':'currently can\'t run benchmarks without defined executable on remote platform'}

          if sdi!='yes':
             r=ck.access({'action':'init_device',
                          'module_uoa':cfg['module_deps']['platform'],
                          'os_dict':tosd,
                          'device_id':tdid})
             if r['return']>0: return r

          rs=tosd['remote_shell'].replace('$#device#$',tdid)

          # Copy exe
          y=tosd['remote_push'].replace('$#device#$',tdid)+' '+target_exe+' '+rdir+target_exe
          if o=='con':
             ck.out(sep)
             ck.out(y)
             ck.out('')

          ry=os.system(y)
          if ry>0:
             return {'return':1, 'error':'copying to remote device failed'}

          # Set chmod
          se=tosd.get('set_executable','')
          if se!='':
             y=rs+' '+se+' '+rdir+target_exe
             if o=='con':
                ck.out(sep)
                ck.out(y)
                ck.out('')

             ry=os.system(y)
             if ry>0:
                return {'return':1, 'error':'making binary executable failed on remote device'}

          # Copy explicit input files, if first time
          rif=rt.get('run_input_files',[])
          if sdi!='yes':
             for df in rif:
                 # Push data files to device
                 y=tosd['remote_push'].replace('$#device#$',tdid)+' '+os.path.join(p,df)+' '+rdir+stdirs+df
                 if o=='con':
                    ck.out(sep)
                    ck.out(y)
                    ck.out('')

                 ry=os.system(y)
                 if ry>0:
                    return {'return':1, 'error':'copying to remote device failed'}

       # Loading dataset
       if dduoa!='':
          rx=ck.access({'action':'load',
                        'module_uoa':dmuoa,
                        'data_uoa':dduoa})
          if rx['return']>0: return rx
          dd=rx['dict']
          dp=rx['path']

          if remote=='yes':
             c=c.replace('$#dataset_path#$','')
          else:
             c=c.replace('$#dataset_path#$',dp+sdirs)

          dfiles=dd.get('dataset_files',[])
          if len(dfiles)>0:
             for k in range(0, len(dfiles)):
                 df=dfiles[k]
                 kk='$#dataset_filename'
                 if k>0: kk+='_'+str(k)
                 kk+='#$'
                 c=c.replace(kk, df)

                 if remote=='yes' and sdi!='yes':
                    # Push data files to device, if first time
                    y=tosd['remote_push'].replace('$#device#$',tdid)+' '+os.path.join(dp,df)+' '+rdir+stdirs+df
                    if o=='con':
                       ck.out(sep)
                       ck.out(y)
                       ck.out('')

                    ry=os.system(y)
                    if ry>0:
                       return {'return':1, 'error':'copying to remote device failed'}

          rcm=dd.get('cm_properties',{}).get('run_time',{}).get('run_cmd_main',{})
          for k in rcm:
              kv=rcm[k]
              c=c.replace('$#'+k+'#$',kv)

          misc['dataset_uoa']=dduoa

       # Check if redirect output
       rco1=rt.get('run_cmd_out1','')
       rco2=rt.get('run_cmd_out2','')

       if rco1!='': c+=' '+stro+' '+rco1
       if rco2!='': c+=' '+stre+' '+rco2

       sb+=c+'\n'

       fn=''

       # Clean output files
       rof=rt.get('run_output_files',[])
       for df in rof:
           if remote=='yes':
              # Push data files to device
              y=rs+' '+tosd['delete_file']+ ' '+rdir+stdirs+df
              if o=='con':
                 ck.out('')
                 ck.out(y)
                 ck.out('')

              ry=os.system(y)
           else:
              if os.path.isfile(df): 
                 os.remove(df)

       # Calibrate execution time (to make it longer and minimize system variation, 
       #   if supported)
       csb=sb
       orepeat=repeat
       calibrate_success=False
       
       xcn_max=i.get('calibration_max','')
       if xcn_max=='': xcn_max=cfg['calibration_max']
       cn_max=int(xcn_max)

       cn=0
       while True:
          if sc!='yes':
             ck.out('')
             ck.out('### Calibration: Current REPEAT number = '+str(repeat))

          sb=csb
          if sc!='yes' and 'CT_REPEAT_MAIN' in env1 and repeat!=-1:
             sb=sb.replace('$#repeat#$', str(repeat))

          # Prepare execution
          if remote=='yes':
             # Prepare command as one line
             y=''

             x=sb.split('\n')
             for q in x:
                 if q!='':
                    if y!='': y+=envtsep
                    y+=' '+q

             y=rs+' '+tosd['change_dir']+' '+rdir+envtsep+' '+y
          else:
             # Record to tmp batch and run
             rx=ck.gen_tmp_file({'prefix':'tmp-', 'suffix':sext, 'remove_dir':'yes'})
             if rx['return']>0: return rx
             fn=rx['file_name']

             rx=ck.save_text_file({'text_file':fn, 'string':sb})
             if rx['return']>0: return rx

             y=''
             if sexe!='':
                y+=sexe+' '+sbp+fn+envsep
             y+=' '+scall+' '+sbp+fn
                
          if o=='con':
             ck.out(sep)
             ck.out(y)
             ck.out('')

          # Execute command 
          sys.stdout.flush()
          start_time1=time.time()
          rx=os.system(y)
          exec_time=time.time()-start_time1

          if i.get('skip_clean_after','')!='yes':
             if fn!='' and os.path.isfile(fn): os.remove(fn)

          # Check calibration
          if sc=='yes' or repeat==-1: 
             calibrate_success=True
             break

          orepeat=repeat
          if exec_time<0.5: repeat*=10
          elif 0.8<(calibrate_time/exec_time)<1.4: 
             calibrate_success=True
             break
          else: 
             repeat*=float(calibrate_time/exec_time)
          repeat=int(repeat)

          if repeat==orepeat:
             calibrate_success=True
             break

          if o=='con' and sc!='yes':
             ck.out('')
             ck.out('### Calibration: time='+str(exec_time)+'; CT_REPEAT_MAIN='+str(orepeat)+'; new CT_REPEAT_MAIN='+str(repeat))

          if cn>=cn_max:
             return {'return':1, 'error':'calibration failed'}

          cn+=1

       if sc!='yes' and repeat!=-1:
          if calibrate_success==False:
             return {'return':1, 'error':'calibration problem'}

       # Pull files from the device if remote
       if remote=='yes':
          rof=rt.get('run_output_files',[])
          for df in rof:
              # Push data files to device
              y=tosd['remote_pull'].replace('$#device#$',tdid)+' '+rdir+stdirs+df+' '+df
              if o=='con':
                 ck.out('')
                 ck.out(y)
                 ck.out('')

              ry=os.system(y)

       ccc['execution_time']=exec_time
       if repeat>0:
          ccc['normalized_execution_time']=exec_time/repeat
          ccc['repeat']=repeat
          misc['calibration_success']=calibrate_success

       if rx>0 and vcmd.get('ignore_return_code','').lower()!='yes':
          misc['run_success']='no'
       else:
          misc['run_success']='yes'

       ccc['execution_time_with_module']=time.time()-start_time

       if o=='con':
          ck.out('')
          x='Execution time: '+('%.3f'%exec_time)
          if repeat>1:
             x+=' sec.; Repetitions: '+str(repeat)+'; Normalized execution time: '+('%.6f'%(exec_time/repeat))+' sec.'
          ck.out(x)

    return {'return':0, 'tmp_dir':rcdir, 'misc':misc, 'characteristics':ccc, 'deps':deps}

##############################################################################
# clean program work and tmp files

def clean(i):
    """
    Input:  {
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    i['sub_action']='clean'
    return process(i)

##############################################################################
# compile program

def compile(i):
    """
    Input:  {
              (repo_uoa)   - program repo UOA
              (module_uoa) - program module UOA
              data_uoa     - program data UOA

              (process_in_tmp)
              (tmp_dir)
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              Output of the last compile from function 'process_in_dir'
            }

    """

    i['sub_action']='compile'
    return process(i)

##############################################################################
# run program

def run(i):
    """
    Input:  {
               (cmd_key)     - cmd key
               (dataset_uoa) - dataset UOA
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    i['sub_action']='run'
    return process(i)

##############################################################################
# auto-tuning program

def autotune(i):
    """
    Input:  {
              (repo_uoa)   - program repo UOA
              (module_uoa) - program module UOA
              data_uoa     - program data UOA

              (process_in_tmp)
              (tmp_dir)

            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    import copy
    import os
    import random

    # Prepare copy of input to reuse later
    ic=copy.deepcopy(i)

    pp=os.getcwd()

    ni=i.get('number_of_iterations',0)
    try: ni=int(ni)
    except Exception as e: pass

    srm=i.get('stat_repetitions',0)
    try: srm=int(srm)
    except Exception as e: pass

    deps={}

    dflag=i.get('default_flag','')

    eruoa=i.get('experiment_repo_uoa','')
    euoa=i.get('experiment_uoa','')

    # Hack
    cduoa=i.get('compiler_desc_uoa','')
    if cduoa!='':
       rx=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['compiler'],
                     'data_uoa':cduoa})
       if rx['return']>0: return rx
       cm=rx['dict']
       cc=cm.get('all_compiler_flags_desc',{})

    sdi='no'

    for m in range(0,ni+1):
        grtd=i.get('generate_rnd_tmp_dir','')
        if grtd=='': grtd='yes'
        tmp_dir=i.get('tmp_dir','')

        ck.out(sep)
        ck.out('Iteration: '+str(m))
        ck.out('')

        ii=copy.deepcopy(ic)
        ii['deps']=deps

        # Describing experiment
        dd={}

        dd['input']=ii
        dd['choices']={}
        dd['characteristics']={}
        dd['features']={}
        dd['misc']={}

        ##########################################################################################
        # Generate flags
        cflags=dflag
        if m!=0:
           cflags='-O3'
           for q in cc:
               if q!='##base_flag':
                  qx=cc[q]

                  stat=random.randrange(0, 1000)
                  if stat>900:
                     cqx=qx.get('choice',[])
                     lcqx=len(cqx)
                     if lcqx>0:
                        ln=random.randrange(0, lcqx)
                        cflags+=' '+cqx[ln]
                     else:
                        cflags+=''

        ck.out('Flags: '+cflags)

        ii['flags']=cflags

        dd['features']['compiler_flags']=cflags

        ##########################################################################################
        # Compile 
        os.chdir(pp)

        if grtd=='yes':
           ii['generate_rnd_tmp_dir']='yes'
        else:
           ii['generate_rnd_tmp_dir']=''

        ck.out('')
        rx=compile(ii)
        if rx['return']>0: return rx 

        deps=rx['deps']
        cmisc=rx['misc']
        cch=rx['characteristics']

        tmp_dir=cmisc['tmp_dir']
        tp=cmisc['path']

        xct=cch.get('compilation_time',-1)
        xos=cch.get('obj_size',-1)

        dd['characteristics']['compile']=cch
        dd['misc']['compile']=cmisc

        if xos>0:
           ##########################################################################################
           # Run
           ii['deps']=deps
           ii1=copy.deepcopy(ii)

           repeat=-1

           for sr in range(0, srm):
               ck.out('')
               ck.out('------------------- Statistical reptition: '+str(sr))
               ii=copy.deepcopy(ii1)

               os.chdir(pp)

               ii['skip_device_init']=sdi
               if repeat!=-1:
                  ii['repeat']=repeat

               if tmp_dir!='':
                  ii['tmp_dir']=tmp_dir

               rx=run(ii)
               if rx['return']>0: return rx

               if sdi!='yes': sdi='yes'

               rmisc=rx['misc']
               rch=rx['characteristics']

               rsucc=rmisc.get('run_success','')
               dataset_uoa=rmisc.get('dataset_uoa','')
               xrt=rch.get('execution_time',-1)

               repeat=rch.get('repeat',-1)
               xnrt=rch.get('normalized_execution_time',-1)

               if rsucc=='yes' and xrt>0:
                  ck.out('')
                  ck.out('###### Compile time: '+str(xct)+', obj size: '+str(xos)+', run time: '+str(xrt)+', repeat: '+str(repeat))
                  ck.out('')

               dd['characteristics']['run']=rch
               dd['misc']['run']=rmisc

               ##########################################################################################
               # For now Process/record in expeirment, only if compile was successful
               # TBD: For compiler/architecture testing purposes, we may want to record failed cases in another repo

               ck.out(sep)
                  
               ie={'action':'add',

                   'module_uoa':'experiment',

                   'ignore_update':'yes',

                   'experiment_repo_uoa': eruoa,
                   'experiment_uoa':euoa,

#                   'search_point_by_features':'yes',
#                   'process_multi_keys':['characteristics','features'],
                   'record_all_subpoints':'yes',

                   'search_point_by_features':'yes',
                   
                   'force_new_entry':'yes',

                   'sort_keys':'yes',
                   'out':'con',
                   'dict':dd}

               rx=ck.access(ie)
               if rx['return']>0: return rx

        if tmp_dir!='' and tmp_dir!='tmp' and i.get('skip_clean_after','')!='yes':
           os.chdir(tp)
           import shutil
           shutil.rmtree(tmp_dir)

    return {'return':0}

##############################################################################
# crowdtuning program

def crowdtune(i):
    """
    Input:  {
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    ck.out ('tbd: crowdtuning program')

    return {'return':0}
